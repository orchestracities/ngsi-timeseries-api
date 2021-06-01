"""
Bare-bones runtime system to execute ``Tasklet``s as RQ jobs.
Notice you shouldn't start QuantumLeap WQ directly through the RQ CLI
since there are some QuantumLeap-specific parameters that need setting
for QL ``Tasklet``s to be executed as RQ jobs, which is why we've got
the wrapper functions in this module.
"""

from multiprocessing import Pool
import os
from time import sleep
from typing import Optional

from rq import Queue, SimpleWorker, Worker
from rq.job import Job

from server.telemetry.monitor import Monitor
from wq.core.cfg import queue_names, redis_connection, log_level
from wq.core.mgmt import _task_info_from_rq_job
from wq.core.task import RqExcMan


# NOTE (Running RQ Workers)
#
# 1. Run Worker in its own process since it installs signal handlers.
# According to
# - https://docs.python.org/3/library/signal.html#signals-and-threads
#   "Python signal handlers are always executed in the main Python thread
#   of the main interpreter, even if the signal was received in another
#   thread"
# So you could wind up in a situation where most of the Worker threads won't
# execute their signal handlers. Those handlers kill the "Work Horse" process
# of each Worker, so we wouldn't have a clean exit.
#
# 2. Don't use the daemon flag when starting a Worker process.
# According to
# - https://docs.python.org/3/library/multiprocessing.html
#   "daemonic process is not allowed to create child processes"
# But Worker creates a new process, the "Work Horse" to run each task fetched
# from the queue.
#
# 3. Worker processes tasks serially.
# One task at a time in its own "Work Horse", but no two Work Horses get
# forked simultaneously. Unless you use SimpleWorker instead of the default
# Worker, in which case no Work Horse gets forked, the task gets run in
# the main process thread.


class TelemetryWorker(SimpleWorker):
    """
    Extend RQ ``Worker`` to collect task duration samples using QuantumLeap
    telemetry framework.
    """

    @staticmethod
    def _new_monitor(monitoring_dir: str) -> Monitor:
        return Monitor(monitoring_dir=monitoring_dir,
                       with_runtime=False,
                       with_profiler=False)

    def __init__(self, *args, **kwargs):
        monitoring_dir = kwargs.pop('monitoring_dir')
        self.monitor = self._new_monitor(monitoring_dir)
        self.duration_sample_id = ''
        super().__init__(*args, **kwargs)

    def register_birth(self):
        os.makedirs(self.monitor.monitoring_dir(), exist_ok=True)
        super().register_birth()

    def execute_job(self, job, queue):
        task_info = _task_info_from_rq_job(job)
        key = f"task: {task_info.runtime.task_type}"
        self.duration_sample_id = self.monitor.start_duration_sample()
        try:
            super().execute_job(job, queue)
        finally:
            self.monitor.stop_duration_sample(key, self.duration_sample_id)

    def register_death(self):
        self.monitor.stop()
        super().register_death()


def _new_rq_worker() -> Worker:
    return SimpleWorker(queues=queue_names(),
                        connection=redis_connection(),
                        queue_class=Queue,                              # (1)
                        job_class=Job,                                  # (2)
                        exception_handlers=[RqExcMan.exc_handler])      # (3)
# NOTE
# 1. We're relying on the default Queue class in our code, so this is just
# a reminder not to use a custom class which vanilla RQ lets you do.
# Technically not needed since if not given or set to None, the Worker
# will default it to Worker.queue_class which happens to be rq.Queue.
# 2. Ditto for the Job class.
# 3. We install only one exception handler to manage retries since RQ
# doesn't let you easily bail out of a retry cycle. In fact, if you've
# got n retries, then RQ will retry the task n times, but on catching
# an exception you could realise you can't recover from the error, so
# it'd be pointless to retry. That exception handler breaks out of the
# retry cycle if you raise the stop exception.
# 4. We're happy with RQ's default values for all other params, in particular
# name will be a GUID, see __init__.


def _new_telemetry_worker(monitoring_dir: str) -> Worker:
    return TelemetryWorker(monitoring_dir=monitoring_dir,
                           queues=queue_names(),
                           connection=redis_connection(),
                           queue_class=Queue,                            # (1)
                           job_class=Job,                                # (2)
                           exception_handlers=[RqExcMan.exc_handler])    # (3)
# NOTE. See notes (1), (2), (3) above.


def _start_worker(burst_mode: bool = False,
                  max_tasks: Optional[int] = None,
                  monitoring_dir: Optional[str] = None):
    if monitoring_dir:
        w = _new_telemetry_worker(monitoring_dir)
    else:
        w = _new_rq_worker()
    w.work(with_scheduler=True,          # (1)
           burst=burst_mode,             # (2)
           max_jobs=max_tasks,           # (3)
           logging_level=log_level())    # (4)
# NOTE
# 1. Scheduler. Required since we use retries. (Failed tasks get scheduled
# for execution at a later time.)
# 2. Burst mode. If true, the worker will drain the queue and exit.
# 3. Max tasks. If given, the worker exits after processing that many jobs.
# 4. Log level. We use one of the IDs known to the ``logging`` lib to avoid
# a situation where the worker bombs out on start up b/c of an exception
# thrown by the ``logging`` lib.
# 5. For now we'll keep RQ's default values for all other params, but going
# forward we could change some, e.g. the log format.


class WorkerPool:

    def __init__(self, pool_size: int,
                 burst_mode: bool = False,
                 max_tasks: Optional[int] = None,
                 monitoring_dir: Optional[str] = None):
        self.pool_size = pool_size
        self.burst_mode = burst_mode
        self.max_tasks = max_tasks
        self.monitoring_dir = monitoring_dir

    def _run_worker(self, _):    # (*)
        _start_worker(self.burst_mode, self.max_tasks, self.monitoring_dir)
# NOTE. Dummy arg.
# Proc pool's map needs a function w/ one arg, otherwise it'll bomb out.

    def start(self):
        with Pool(processes=self.pool_size) as p:                     # (1)
            while True:                                               # (2)
                try:
                    p.map(self._run_worker, range(self.pool_size))    # (3)
                except Exception as e:
                    print(e)

                if self.burst_mode:                                   # (4)
                    sleep(1)
# NOTE
# 1. Self-healing. Unless both burst_mode=False and max_tasks=None, Workers
# will exit after a while. So we avoid RQ workers running for too long and
# perhaps leaking resources. (Possibly not needed since the RQ code seems
# solid, so potentially you could keep the Workers going forever w/o any
# trouble.) Plus, Pool does some book keeping to avoid leaking resources,
# have a look at the docs. But consider setting ``maxtasksperchild`` to make
# sure to replace pool processes w/ fresh ones after a while. (Need to think
# about how that'd gel w/ boost mode and max tasks though...)
# 2. Exit. If you kill the main process, the pool should catch the kill signal
# and send a sigint to the RQ workers in the pool. Since Worker installs signal
# handlers, we should exit gracefully. At least that's the theory. I haven't
# tested this properly. In particular, we should test the case when Worker
# processes keep on looping forever, i.e. burst_mode=False and max_tasks=None.
# Is the above set up going to guarantee a clean exit in all cases? Or could
# we wind up with orphan/zombie processes?! Maybe worth coding this explicitly
# with `atexit` clean up to reap Workers...
# 3. Forking efficiency. The pool won't fork new processes on every call to
# map, but reuse existing processes. If a process in the pool dies, then a
# new one will replace it. This is essential for running in burst mode where
# you definitely don't want to fork new processes every time a Worker exits
# since that could happen every second if the queue is empty! Use e.g.
# `htop -F python -t` or `pstree -s python` after starting WQ w/ a pool to
# see what's actually going on. (Even with an empty queue and burst_mode=True
# you should still see the same processes being kept around for a long while.)
# But consider using: mp.set_start_method('forkserver')
# 4. Empty queue. When in burst mode, Workers drain the queues and then exit.
# So we wait a bit before getting back in the loop since we know the queue is
# empty right now.


def start(pool_size: Optional[int] = None,
          burst_mode: bool = False,
          max_tasks: Optional[int] = None,
          monitoring_dir: Optional[str] = None):
    if pool_size is None or pool_size <= 1:
        _start_worker(burst_mode, max_tasks, monitoring_dir)    # (1)
    else:
        wp = WorkerPool(pool_size, burst_mode, max_tasks, monitoring_dir)
        wp.start()                                              # (2)
# NOTE
# 1. RQ compat mode. For all intents and purposes, this is equivalent to
# starting QuantumLeap WQ with the ``rq worker --with-scheduler`` command
# and possibly passing in burst mode and/or max jobs.
# 2. Parallelism. Still experimental, only use for testing. In fact, funnily
# enough, if you start two worker processes and then kill the main process:
#
#   $ python wq up -w 2
#   09:51:48 Worker rq:worker:d0... started...
#   09:51:48 Subscribing to channel rq:pubsub:d0...
#   09:51:48 Worker rq:worker:d3... started...
#   09:51:48 Subscribing to channel rq:pubsub:d3...
#   09:51:48 *** Listening on default...
#   09:51:48 *** Listening on default...
#   09:51:48 Trying to acquire locks for default
#   09:51:48 Trying to acquire locks for default
#
# Now kill the the process (^C)
#
#    ^CProcess SpawnPoolWorker-1:
#    09:51:59 Warm shut down requested
#    09:51:59 Cold shut down
#
# It still hangs though. Kill again (^C)
#
#   ^C09:52:32 Cold shut down
#
#   Aborted!
#
# Signals not properly forwarded by the pool? Also, why the "Cold shut down"?
# This is the result of Worker calling request_force_stop which should only
# happen if Worker gets two ^C in a row. In fact, if you run ``rq worker``
# and kill it, you'll only see a "Warm shut down requested". Go figure!
# See note (2) above about pool exit. Also make sure dead Worker hashes
# get removed from Redis eventually, which they should since there's a
# 1 min TTL on the hash if memory serves---look at the RQ source.
