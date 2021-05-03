from multiprocessing import Pool
from rq import Connection, Worker

from wq.core.cfg import queue_names, redis_connection


def run_tasks(_):  # proc pool map needs fn w/ one arg
    # TODO need better init process. eyeball rq/cli/cli.py.
    with Connection(connection=redis_connection()):
        w = Worker(queues=queue_names())   # name will be a GUID, see __init__
        w.work(burst=True,           # True = drain queues, then exit
               with_scheduler=True)  # need this for scheduling retries

# NOTE
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
# forked simultaneously.


# TODO consider using: mp.set_start_method('forkserver')

def run():
    pool_size = 2  # TODO make configurable
    with Pool(processes=pool_size) as pool:
        while True:
            try:
                pool.map(run_tasks, range(pool_size))
            except Exception as e:
                print(e)
            # sleep if q empty...
            from time import sleep
            print('going to sleep')
            sleep(1)
            print('got up!')

# TODO lame approach, recipe for disaster.
#
# NOTE. RQ Worker exits on empty queue so we avoid workers running for too
# long and perhaps leaking resources. But it looks like the RQ code is solid
# so a better option could be to set burst=False and let the Worker take care
# of itself.
#
# TODO is the above set up going to guarantee a clean exit in all cases if
# we set burst=False? Or could we wind up with orphan/zombie processes?!
# Maybe worth coding this explicitly with `atexit` clean up to reap Workers...
#
# TODO need health endpoint if not running inside QL Web


if __name__ == '__main__':
    run()
