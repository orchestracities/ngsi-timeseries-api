"""
Description
-----------
Convenience module to provide a simple interface for common monitoring
scenarios. Using this module you can easily:

* time the duration of selected code blocks;
* turn on the Python built-in profiler (cProfile);
* gather garbage collection and OS resource usage metrics.

Duration, GC and OS measurements are assembled in time series. Every time
you sample a duration, a corresponding measurement is added to an underlying
duration series at the current time point. GC and OS metrics, if enabled,
work similarly, except they're automatically gathered in a background thread
every second. Notice we use a nanosecond-resolution, high-precision timer
under the bonnet. Time series data are collected in a memory buffer which
gets flushed to file as soon as the buffer fills. Files are written to a
directory of your choice.


Concurrency and performance
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The whole data collection process, from memory to file, is designed to be
efficient and have a low memory footprint in order to minimise impact on
the runtime performance of the process being monitored and guarantee accurate
measurements. At the same time, it is thread-safe and can even be used by
multiple processes simultaneously, e.g. a Gunicorn WSGI app configured with
a pre-forked server model. (See the documentation of the ``flush`` module
about parallel reader/writer processes.)

As a frame of reference, average overhead for collecting a duration sample
is 0.31 ms. Memory gets capped at 1 MiB as noted below. (You can use the
overhead gauge script in the tests directory to experiment yourself.)


Output files
^^^^^^^^^^^^
Time series data are collected in a memory buffer which gets flushed to
file when the buffer's memory grows bigger than 1 MiB. Files are written to
a directory of your choice with file names having the following prefixes:
the value of ``DURATION_FILE_PREFIX`` for duration series, the value of
``RUNTIME_FILE_PREFIX`` for GC & OS metrics, and ``PROFILER_FILE_PREFIX``
for profiler data. The file format is CSV and fields are arranged as
follows:

* **Timepoint**: time at which the measurement was taken, expressed as number
    of nanoseconds since the epoch. (Integer value.)
* **Measurement**: sampled quantity. (Float value.)
* **Label**: name used to identify a particular kind of measurement when
    sampling. (String value.)
* **PID**: operating system ID of the process that sampled the quantity.

Out of convenience, the CSV file starts with a header of: ``Timepoint,
Measurement, Label, PID``.


Usage
^^^^^
You start a monitoring session with a call to the ``start`` function
::
    import server.telemetry.monitor as monitor

    monitor.start(monitoring_dir='/my/output/',  # where to output files
                  with_runtime=True,             # enable GC & OS sampling
                  with_profiler=False)           # but keep profiler off

This function should be called exactly once, so it's best to call it from
the main thread when the process starts. There's also a ``stop`` function
you should call just before the process exits to make sure all memory buffers
get flushed to file:
::
    monitor.stop()

This function too should be called exactly once. With set-up and tear-down
out of the way, let's have a look at how to time a code block:
::
    sample_id = monitor.start_duration_sample()       # start timer
    try:
        # do stuff
    finally:
        key = 'my code block id'      # unique name for this series
        monitor.stop_duration_sample(key, sample_id)  # stop timer

Now every time this block of code gets hit, a new duration sample ends up
in the "my code block id" series. If you later open up the duration file
where the series gets saved, you should be able to see something similar
to
::
    Timepoint, Measurement, Label, PID
        ...
    1607092101580206000, 0.023, "my code block id", 5662
        ...
    1607092101580275000, 0.029, "my code block id", 5662
        ...

Timing your code with ``try/finally`` clauses like we did earlier is
quite verbose, so we have a context decorator you can use to get rid
of the boilerplate. This code snippet is equivalent to the one we saw
earlier:
::
    from server.telemetry.monitor import time_it

    with time_it(label='my code block id'):
        # do stuff

``time_it`` wraps the code block following the ``with`` statement to
run the same timing instructions we wired in manually earlier. And it
works with functions too:
::
    @time_it(label='my_func')
    def my_func():
        # do stuff

Notice when we called the ``start`` method earlier, we turned on
collection of runtime metrics by passing in: ``with_runtime=True``.
With runtime metrics collection enabled, a background
thread gathers GC and OS data (CPU time, memory, etc.) as detailed in
the documentation of ``GCSampler`` and ``ProcSampler``. Another thing
you can do is turn on the profiler when calling the ``start`` function.
In that case, when the process exits you'll have a profile data file
you can import into the Python profiler's stats console, e.g.
::
    python -m pstats profiler.5662.data  # 5662 is the process' PID

Finally, here's a real-world example of using this module with Gunicorn
to record the duration of each HTTP request in time series (one series
for each combination of path and verb) as well as GC and OS metrics.
To try it out yourself, start Gunicorn with a config file containing
::
    import os
    import server.telemetry.monitor as monitor


    bind = "0.0.0.0:8080"
    workers = 2               # pre-fork model (two processes)
    worker_class = 'gthread'  # with threads,
    threads = 2               # two of them for each process
    loglevel = 'debug'


    monitoring_dir = '_monitoring'  # output files go in ./_monitoring

    # init monitoring with duration and runtime samplers just after Gunicorn
    # forks the worker process.
    def post_worker_init(worker):
        os.makedirs(monitoring_dir, exist_ok=True)
        monitor.start(monitoring_dir=monitoring_dir,
                      with_runtime=True,
                      with_profiler=False)

    # start the request timer just before Gunicorn hands off the request
    # to the WSGI app; stash away the sample ID in the request object so
    # we can use it later.
    def pre_request(worker, req):
        req.duration_sample_id = monitor.start_duration_sample()

    # stop the request timer as soon as the WSGI app is done with the
    # request; record request duration in a time series named by combining
    # HTTP path and verb.
    def post_request(worker, req, environ, resp):
        key = f"{req.path} [{req.method}]"
        monitor.stop_duration_sample(key, req.duration_sample_id)

    # flush any left over time series data still buffered in memory just
    # before the process exits.
    def worker_exit(server, worker):
        monitor.stop()

"""

from contextlib import ContextDecorator
from cProfile import Profile
import os
from threading import Lock
from typing import Optional

from server.telemetry.observation import ObservationBucket
from server.telemetry.flush import flush_to_csv
from server.telemetry.sampler import DurationSampler, RuntimeBackgroundSampler


DURATION_FILE_PREFIX = 'duration'
RUNTIME_FILE_PREFIX = 'runtime'
PROFILER_FILE_PREFIX = 'profiler'


def _new_bucket(monitoring_dir: str, prefix: str) -> ObservationBucket:
    return ObservationBucket(
        empty_action=flush_to_csv(
            target_dir=monitoring_dir, filename_prefix=prefix)
    )


def _new_duration_sampler(monitoring_dir: str) -> DurationSampler:
    bucket = _new_bucket(monitoring_dir, DURATION_FILE_PREFIX)
    return DurationSampler(bucket)


def _start_runtime_sampler(monitoring_dir: str) -> ObservationBucket:
    bucket = _new_bucket(monitoring_dir, RUNTIME_FILE_PREFIX)
    RuntimeBackgroundSampler(bucket).spawn()  # (*)
    return bucket
# NOTE. Safe empty action. You can only ever use ``RuntimeBackgroundSampler``
# if the bucket's action can be killed at random without wreaking havoc.
# Since ``flush_to_csv`` writes files to the monitoring dir atomically, we
# can safely do this: all that can happen is that a tiny amount of data still
# in the buffer doesn't get written to the monitoring dir. The amount if any
# will be small b/c we call the bucket's empty method just before quitting,
# see what the stop method below does.


def _profiler_file_pathname(monitoring_dir: str) -> str:
    pid = os.getpid()
    file_name = f"{PROFILER_FILE_PREFIX}.{pid}.data"
    return os.path.join(monitoring_dir, file_name)


class Monitor:

    def __init__(self, monitoring_dir: str,
                 with_runtime: bool = False,
                 with_profiler: bool = False):
        self._monitoring_dir = monitoring_dir
        self._duration_sampler = _new_duration_sampler(monitoring_dir)
        self._runtime_bucket = None
        self._profiler = None
        self._lock = Lock()

        if with_runtime:
            self._runtime_bucket = _start_runtime_sampler(monitoring_dir)

        if with_profiler:
            self._profiler = Profile()
            self._profiler.enable()

    def monitoring_dir(self) -> str:
        return self._monitoring_dir

    def start_duration_sample(self) -> str:
        return self._duration_sampler.sample()

    def stop_duration_sample(self, label: str, sample_id: str):
        self._duration_sampler.collect(label, sample_id)

    def stop(self):
        if self._profiler:
            with self._lock:
                self._profiler.disable()
                outfile = _profiler_file_pathname(self._monitoring_dir)
                self._profiler.dump_stats(outfile)

        self._duration_sampler.bucket().empty()
        if self._runtime_bucket:
            self._runtime_bucket.empty()


_monitor: Optional[Monitor] = None


def start(
        monitoring_dir: str,
        with_runtime: bool = False,
        with_profiler: bool = False):
    """
    Create a process-wide singleton monitor object to collect time series.
    You should call this function early, when the process starts and in the
    main thread before spawning other threads.

    :param monitoring_dir: where to output time series and profiler data files.
    :param with_runtime: enable gathering GC and OS-level data.
    :param with_profiler: turn on profiler.
    """
    global _monitor
    _monitor = Monitor(monitoring_dir, with_runtime, with_profiler)

    # NOTE. Thread-safety. Not worth making this thread-safe. If people stick
    # to the docs, then start gets called when there are no other threads than
    # main.


def start_duration_sample() -> str:
    """
    Start a duration sample. This is just a convenience wrapper around
    ``DurationSampler.sample``, see there for usage.
    """
    if _monitor:
        return _monitor.start_duration_sample()
    return ''


def stop_duration_sample(label: str, sample_id: str):
    """
    End a duration sample. This is just a convenience wrapper around
    ``DurationSampler.collect``, see there for usage.
    """
    if _monitor:
        _monitor.stop_duration_sample(label, sample_id)


def stop():
    """
    Ends the monitoring session. Call this just before the process exits.
    The assumption is that this function gets called **exactly** once.
    """
    if _monitor:
        _monitor.stop()

    # NOTE. Thread-safety. Not worth making this thread-safe. If people stick
    # to the docs, then there's no issues.


class time_it(ContextDecorator):
    """
    Context decorator to time how long a function or a code block takes to run.
    """

    def __init__(self, label: str):
        """
        Create a new instance.

        :param label: a name to identify the time series where durations
            of the timed function or code block should be added.
        """
        self._label = label
        self._sample_id: Optional[str] = None

    def __enter__(self):
        self._sample_id = start_duration_sample()
        return self

    def __exit__(self, *exc):
        stop_duration_sample(self._label, self._sample_id)
        return False
