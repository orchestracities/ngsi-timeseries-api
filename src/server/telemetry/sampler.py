"""
Samplers to measure durations and garbage collection.
You instantiate a sampler with an ``ObservationBucket`` where sampled time
series get buffered. The bucket (memory buffer) is thread-safe and gets
automatically flushed to secondary storage when it fills up.
"""

import gc
from resource import getrusage, RUSAGE_SELF
from threading import Thread
from time import perf_counter, sleep
from uuid import uuid4

from server.telemetry.observation import ObservationBucket, observe, \
    observe_many


class Timer:
    """
    Thread-safe timer.

    Examples:

        >>> from time import sleep
        >>> timer = Timer()

        >>> outer_timer_id = timer.start()
        >>> sleep(0.1)

        >>> inner_timer_id = timer.start()
        >>> sleep(0.1)
        >>> inner_duration = timer.stop(inner_timer_id)

        >>> sleep(0.1)
        >>> outer_duration = timer.stop(outer_timer_id)

        >>> outer_duration - inner_duration > 0.2
        True
    """

    def __init__(self):
        """
        Create a new instance.
        """
        self._timers = {}

    @staticmethod
    def _new_timer_id() -> str:
        timer_id = uuid4()
        return timer_id.hex

    def start(self) -> str:
        """
        Start a timer.

        :return: the timer ID.
        """
        timer_id = self._new_timer_id()  # unique, avoids race conditions.
        self._timers[timer_id] = perf_counter()

        return timer_id

    def stop(self, timer_id) -> float:
        """
        Stop a previously started timer and compute how much time has elapsed
        since starting it.

        :param timer_id: the timer ID returned by the start call.
        :return: time elapsed, in fractional seconds, from the start call.
        """
        duration = perf_counter() - self._timers.pop(timer_id)
        return duration
        # NOTE. pop gets rid of the timer to keep memory footprint small


class DurationSampler:
    """
    Samples durations, storing them in a given ``ObservationBucket``.

    Examples:

        >>> from time import sleep
        >>> from server.telemetry.observation import measured

        # Create a bucket with an action to print the measured values for the
        # key "k". Set memory threshold to 0 to force calling the action on
        # every write to the underlying observation store.
        >>> def print_it(store): \
                print([f"{measured(v):0.1}" for v in store.get('k',[])])
        >>> bkt = ObservationBucket(empty_action=print_it, memory_threshold=0)

        # Create a sampler with the above bucket as backend store.
        >>> sampler = DurationSampler(bkt)

        >>> sample_id = sampler.sample()
        >>> sleep(0.1)
        >>> sampler.collect('k', sample_id)
        ['0.1']

        >>> sample_id = sampler.sample()
        >>> sleep(0.2)
        >>> sampler.collect('k', sample_id)
        ['0.2']

        # Call the empty method when done sampling to make sure any left over
        # data gets passed to the empty action which can then store it away.
        >>> sampler.bucket().empty()
        []
    """

    def __init__(self, bucket: ObservationBucket):
        """
        Create a new instance.

        :param bucket: backend memory buffer where to store data.
        """
        self._bucket = bucket
        self._timer = Timer()

    def bucket(self) -> ObservationBucket:
        """
        :return: backend memory buffer where data is stored.
        """
        return self._bucket

    def sample(self) -> str:
        """
        Start a duration sample.

        :return: the sample ID.
        """
        return self._timer.start()

    def collect(self, key: str, sample_id: str):
        """
        End the specified duration sample and add it to the samples identified
        by the given key.

        :param key: identifies the duration series where the current sample
            should be added.
        :param sample_id: the sample ID as returned by the sample method when
            the sample was started.
        """
        duration = self._timer.stop(sample_id)
        self._bucket.put(observe(key, duration))


GC_COLLECTIONS = 'gc collections'
"""
Label for the series of total GC collections measured by the ``GCSampler``.
"""
GC_COLLECTED = 'gc collected'
"""
Label for the series of total GC collected items measured by the ``GCSampler``.
"""
GC_UNCOLLECTABLE = 'gc uncollectable'
"""
Label for the series of total GC "uncollectable" items measured by the
``GCSampler``.
"""


class GCSampler:
    """
    Produces aggregate stats about Python garbage collection.
    This class generates the three series below.

    **GC collections**. Each measurement in the series represents the total
    number of times the GC collector swept memory since the interpreter was
    started. (This is the total across all generations.) The series is labelled
    with the value of ``GC_COLLECTIONS``.

    **GC collected**. Each measurement in the series represents the total
    number of objects the GC collector freed since the interpreter was started.
    (This is the total across all generations.) The series is labelled with
    the value of ``GC_COLLECTED``.

    **GC uncollectable**. Each measurement in the series represents the total
    number of objects the GC collector couldn't free since the interpreter was
    started. (This is the total across all generations.) The series is labelled
    with the value of ``GC_UNCOLLECTABLE``.
    """

    def __init__(self, bucket: ObservationBucket):
        """
        Create a new instance.

        :param bucket: backend memory buffer where to store data.
        """
        self._bucket = bucket

    def bucket(self) -> ObservationBucket:
        """
        :return: backend memory buffer where data is stored.
        """
        return self._bucket

    def sample(self):
        """
        Sample the GC, aggregate the data, and add them to the series.
        """
        xs = gc.get_stats()
        data = [(x['collections'], x['collected'], x['uncollectable'])
                for x in xs]
        total_collections, total_collected, total_uncollectable = 0, 0, 0
        for d in data:
            total_collections += d[0]
            total_collected += d[1]
            total_uncollectable += d[2]

        ys = observe_many((GC_COLLECTIONS, total_collections),
                          (GC_COLLECTED, total_collected),
                          (GC_UNCOLLECTABLE, total_uncollectable))

        self._bucket.put(*ys)


PROC_USER_TIME = 'user time'
"""
Label for the user time series produced by the ``ProcSampler``.
"""
PROC_SYSTEM_TIME = 'system time'
"""
Label for the system time series produced by the ``ProcSampler``.
"""
PROC_MAX_RSS = 'max rss'
"""
Label for the maximum RSS series produced by the ``ProcSampler``.
"""


class ProcSampler:
    """
    Collects OS resource usage data about this running process.
    This class generates the three series below.

    **User Time**. Each measurement in the series is the total amount of
    time, in seconds, the process spent executing in user mode. The series
    is labelled with the value of ``PROC_USER_TIME``.

    **System Time**. Each measurement in the series is the total amount of
    time, in seconds, the process spent executing in kernel mode. The series
    is labelled with the value of ``PROC_SYSTEM_TIME``.

    **Maximum RSS**. Each measurement in the series is maximum resident set
    size used. The value will be in kilobytes on Linux and bytes on MacOS.
    The series is labelled with the value of ``PROC_MAX_RSS``.
    """

    def __init__(self, bucket: ObservationBucket):
        """
        Create a new instance.

        :param bucket: backend memory buffer where to store data.
        """
        self._bucket = bucket

    def bucket(self) -> ObservationBucket:
        """
        :return: backend memory buffer where data is stored.
        """
        return self._bucket

    def sample(self):
        """
        Probe process user time, system (kernel) time, maximum RSS and add
        these values to their respective series.
        """
        try:
            os_data = getrusage(RUSAGE_SELF)
            xs = observe_many((PROC_USER_TIME, os_data.ru_utime),
                              (PROC_SYSTEM_TIME, os_data.ru_stime),
                              (PROC_MAX_RSS, os_data.ru_maxrss))
            self._bucket.put(*xs)
        except (OSError, AttributeError):  # AttributeError if os_data is None
            return None


class RuntimeBackgroundSampler:
    """
    Convenience class to sample GC and OS metrics at regular intervals in a
    background daemon thread.
    The thread goes on forever until the program exits, calling ``GCSampler``
    and ``ProcSampler`` every ``sampling_interval`` seconds to collect GC and
    OS-level metrics using a bucket you specify.
    Just before the program exits, you should call the bucket's ``empty``
    method to make sure any left over sampled data still in the memory buffer
    gets processed by the bucket's empty action.

    Usage pattern:
    ::
        # at process start up
        bucket = ObservationBucket(...)
        RuntimeBackgroundSampler(bucket).spawn()

        # background thread collects data...

        # just before the process exits
        bucket.empty()

    Convenient, but not very flexible: there's no way to stop the background
    thread and the thread dies abruptly when the program exits. This means
    ``RuntimeBackgroundSampler`` isn't suitable for buckets with empty actions
    that should't be killed at random.
    """

    def __init__(self, bucket: ObservationBucket,
                 sampling_interval: float = 1.0):
        self._gc_sampler = GCSampler(bucket)
        self._proc_sampler = ProcSampler(bucket)
        self._interval = sampling_interval

    def _run(self):
        while True:
            self._gc_sampler.sample()
            self._proc_sampler.sample()
            sleep(self._interval)

    def spawn(self):
        """
        Start the background sampling thread.
        """
        t = Thread(target=self._run, args=())
        t.daemon = True                        # (*)
        t.start()

    # NOTE. Daemon thread. This makes sure the program won't wait on this
    # thread to complete before exiting, which is what we want b/c of the
    # infinite loop in the run method. The downside is that when the Python
    # interpreter quits, this thread will be interrupted abruptly.
