"""
Thread-safe, low memory footprint, and efficient collection of time-varying
quantities. Time series data are collected in a memory buffer which gets
flushed to permanent storage when the buffer's memory grows bigger a than
a configurable threshold.
"""

from sys import getsizeof
from threading import Lock
from time import time_ns
from typing import Callable, Dict, Generator, List, Tuple, Union


Observation = Tuple[int, float]
"""
A numeric observation at a time point ``t``: ``(t, measurement)``.
The first element is the time at which the measurement was taken and is
expressed as the number of nanoseconds since the epoch. The second element
is the actual quantity measured.
"""
# NOTE. Performance. Using a bare tuple instead of a class to keep memory
# footprint low. In fact, there could be quite a number of these little
# guys in memory during a sampling session...
# Unfortunately integers and floats aren't as light on memory as in other
# languages---e.g. an int is actually an object taking up at least 28 bytes
# on a 64-bit box. See:
# - https://pythonspeed.com/articles/python-integers-memory/
# - https://stackoverflow.com/questions/10365624
#
# NumPy would possibly have a much smaller footprint, but we'd like to keep
# this package self-contained so not to impose any external lib dependency
# on users.

OBSERVATION_MIN_SZ = getsizeof((0, 0.0))
"""
The least amount of memory, in bytes, an observation tuple can possibly
take up on this machine. Typically 56 bytes on a 64-bit architecture.
"""

LabelledObservation = Tuple[int, float, str]
"""
An observation with a string label. Data are flattened in a triple
``(time, measurement, label)``.
"""


def when(data: Union[Observation, LabelledObservation]) -> int:
    """
    The observation's time-point, in nanoseconds since the epoch.

    :param data: the observation data.
    :return: the data's time-point component.
    """
    return data[0]


def measured(data: Union[Observation, LabelledObservation]) -> float:
    """
    The observation's measured quantity.

    :param data: the observation data.
    :return: the data's measurement component.
    """
    return data[1]


def named(data: LabelledObservation) -> str:
    """
    The observation's label.

    :param data: the observation data.
    :return: the data's label component.
    """
    return data[2]


def _split_label(data: LabelledObservation) -> (str, Observation):
    return data[2], data[0:2]


def observe(label: str, measurement: float) -> LabelledObservation:
    """
    Record the given measurement was taken at this exact point in time.

    :param label: a unique name to identify measurements of this kind.
    :param measurement: the measured numeric quantity.
    :return: the corresponding ``LabelledObservation``.

    Examples:

        >>> x = observe('temp', 75.3)
        >>> named(x)
        'temp'
        >>> measured(x)
        75.3
        >>> when(x) > 1606832514068067000  # 1 Dec 2020
        True
    """
    return time_ns(), measurement, label


def observe_many(*labelled_measurements: (str, float)) \
        -> List[LabelledObservation]:
    """
    Record the given measurements were taken at this exact point in time.
    Each measurement comes labelled with a name to identify measurements
    of a given kind.

    :param labelled_measurements: a list of ``(label, measurement)`` pairs.
    :return: the corresponding list of ``LabelledObservation``.

    Examples:

        >>> xs = observe_many(('temp', 75.3), ('pressure', 19.2))
        >>> len(xs) == 2
        True

        >>> when(xs[0]) == when(xs[1])
        True

        >>> named(xs[0])
        'temp'
        >>> measured(xs[0])
        75.3

        >>> named(xs[1])
        'pressure'
        >>> measured(xs[1])
        19.2
    """
    now = time_ns()
    return [(now, d[1], d[0]) for d in labelled_measurements]


ObservationSeries = List[Observation]
"""
A time series of numeric measurements.
"""

ObservationStore = Dict[str, ObservationSeries]
"""
A collection of labelled observation time series. Each label uniquely
identifies a time series.
"""
# NOTE. Memory footprint. It looks like that using a dict with list values
# shouldn't be too bad:
# - https://stackoverflow.com/questions/10264874


def _extend_series(store: ObservationStore, label: str, obs: [Observation]):
    series = store.get(label, [])
    series.extend(obs)
    store[label] = series

    # NOTE. Memory footprint.
    # According to the interwebs, it isn't really worth your while
    # pre-allocating a list with an initial capacity. I have my doubts
    # about this though and the effect of append on GC---i.e. what if
    # the list grows in too small chunks? Is there any data structure
    # we could use? Simple benchmarks show that we shouldn't have an
    # issue here, but I'd still like to figure out to what extent this
    # affects GC and how to optimise.


def observation_store(*ts: LabelledObservation) -> ObservationStore:
    """
    Build an observation store out of the given labelled observations.

    :param ts: the input data.
    :return: the store with the input data.

    Examples:

        >>> observation_store()
        {}

        >>> ts = observe('h', 3.2), observe('k', 1.0), observe('k', 1.1)
        >>> store = observation_store(*ts)
        >>> len(store) == 2
        True

        >>> [measured(x) for x in store['h']]
        [3.2]
        >>> [measured(x) for x in store['k']]
        [1.0, 1.1]
    """
    store = {}
    for t in ts:
        label, ob = _split_label(t)
        _extend_series(store, label, [ob])

    return store


def merge_observation_stores(*ts: ObservationStore) -> ObservationStore:
    """
    Combine observation stores into one. This happens by using a monoidal
    sum ``:+:`` defined on observation stores, so that if ``t1, t2, t3, ...``
    are the input stores the result is ``((t1 :+: t2) :+: t3) :+: ...)``.
    The sum of two stores, ``a :+: b`` is defined as follows. Call ``K`` the
    set of keys from two stores. The result table ``r`` has keys ``k ∈ K``
    and values ``r[k] = a.get(k, []) + b.get(k, [])``.

    :param ts: the observation stores to merge.
    :return: an observation store with series merged from the input stores.

    Examples:

        >>> merge_observation_stores()
        {}

        >>> a_obs = observe_many(('k1', 1.0), ('k1', 2.0), ('k2', 3.0))
        >>> a = observation_store(*a_obs)
        >>> b_obs = observe_many(('k2', 4.0), ('k3', 5.0))
        >>> b = observation_store(*b_obs)

        >>> m = merge_observation_stores(a, b)

        >>> [measured(obs) for obs in m['k1']]
        [1.0, 2.0]
        >>> [measured(obs) for obs in m['k2']]
        [3.0, 4.0]
        >>> [measured(obs) for obs in m['k3']]
        [5.0]
    """
    merged = {}
    for t in ts:
        for k in t:
            _extend_series(merged, k, t[k])

    return merged
    # NOTE. Efficient algo. This function is only used for examples and testing
    # so performance isn't really critical. But it'd be nice to implement an
    # efficient algorithm.


def tabulate(store: ObservationStore) -> \
        Generator[LabelledObservation, None, None]:
    """
    Stream the content of an observation store as a sequence of labelled
    observations.

    :param store: the data source.
    :return: a stream of labelled observations.

    Examples:

        >>> obs = observe_many(('k1', 1.0), ('k1', 2.0), ('k2', 3.0))
        >>> store = observation_store(*obs)
        >>> [(k, m) for (t, m, k) in tabulate(store)]
        [('k1', 1.0), ('k1', 2.0), ('k2', 3.0)]
    """
    for k in store:
        for ob in store[k]:
            yield when(ob), measured(ob), k


class ObservationBuffer:
    """
    Buffers observation series in an observation store.

    Examples:

        >>> buf = ObservationBuffer()
        >>> buf.insert(observe('h', 1.0))
        >>> buf.insert(observe('k', 0.1))
        >>> buf.insert(observe('h', 2.0))
        >>> buf.size()
        2

        >>> tot_bytes = buf.estimate_memory_lower_bound()
        >>> 150 < tot_bytes < 200
        True

        >>> store = buf.flush()
        >>> buf.size() == 0
        True
        >>> len(store) == 2
        True

        >>> [measured(ob) for ob in store['h']]
        [1.0, 2.0]

    """

    def __init__(self):
        """
        Create a new instance with an empty observation store.
        """
        self._store: ObservationStore = {}
        self._memory_lower_bound = 0

    def size(self) -> int:
        """
        :return: number of rows in the store which is the same as the number
            of observation series.
        """
        return len(self._store)

    def estimate_memory_lower_bound(self) -> int:
        """
        :return: the minimum number of bytes the observation store can possibly
            take up in memory.
        """
        return self._memory_lower_bound

    def insert(self, *ts: LabelledObservation):
        """
        Append each labelled observation ``t`` to the series identified by
        ``t``'s label, automatically creating a new series if the label isn't
        present.

        :param ts: the labelled observations to append.
        """
        for t in ts:
            label, ob = _split_label(t)
            _extend_series(self._store, label, [ob])

        self._memory_lower_bound += OBSERVATION_MIN_SZ * len(ts)

    def flush(self) -> ObservationStore:
        """
        Discard the observation store.

        :return: the observation store just discarded.
        """
        s = self._store
        self._store = {}
        return s


ObservationStoreAction = Callable[[ObservationStore], None]
"""
A function that does something with the input observation store.
"""


class ObservationBucket:
    """
    Wraps an observation store to make it thread-safe and periodically
    empty it to reclaim memory. It makes the store work like a (memory)
    bucket, when the bucket is full, it gets emptied into a sink, an
    ``ObservationStoreAction`` that takes the store's content and saves
    it away from memory.

    Examples:

        Create a bucket with an action to print the measured values for
        key "k". Set memory threshold to 0 to force calling the action
        on every write to the underlying observation store.

        >>> def print_it(store): \
                print([measured(v) for v in store.get('k',[])])
        >>> bkt = ObservationBucket(empty_action=print_it, memory_threshold=0)

        Do some sampling.

        >>> bkt.put(*observe_many(('k', 1.0), ('k', 2.0)))
        [1.0, 2.0]

        >>> bkt.put(observe('k', 3.0))
        [3.0]

        Call the empty method when done sampling to make sure any left over
        data gets passed to the empty action which can then store it away.

        >>> bkt.empty()
        []
    """

    def __init__(self,
                 empty_action: ObservationStoreAction,
                 memory_threshold: int = 1 * 2**20
                 ):
        """
        Create a new instance.

        :param empty_action: a function to store the data collected so far.
            It takes a single ``ObservationStore`` and returns nothing. Called
            when the ``memory_threshold`` is reached or the ``empty`` method
            is called.
        :param memory_threshold: the amount of bytes past which the store
            gets emptied. When the memory size of the observation store grows
            bigger than this value, the empty action is automatically invoked.
            Defaults to 1MiB.
        """
        self._buffer = ObservationBuffer()
        self._lock = Lock()
        self._empty_action = empty_action
        self._memory_threshold = memory_threshold

    def put(self, *ts: LabelledObservation):
        """
        Put data into the bucket by calling the underlying store's ``insert``
        method to update observations.

        :param ts: the labelled observations to append to the existing series.
        """
        flushed_store = None
        with self._lock:                         # (1)
            self._buffer.insert(*ts)

            mem = self._buffer.estimate_memory_lower_bound()
            if mem > self._memory_threshold:
                flushed_store = self._buffer.flush()

        if flushed_store:
            self._empty_action(flushed_store)    # (2)

        # NOTES.
        # 1. Locking. It shouldn't affect performance adversely since typically
        # ``put`` gets called after servicing the HTTP request. Also if threads
        # compete for the lock, that time won't be reflected in the samples.
        # 2. Confinement. We use a confinement strategy to avoid locking while
        # the empty action runs. This is safe since we let go of the only ref
        # to the store and passed it on to the empty action.

    def empty(self):
        """
        Empty the bucket. Wipe clean the underlying store but pass the data
        on to the empty action so that it can be stored away from memory.
        """
        with self._lock:
            store = self._buffer.flush()
            self._empty_action(store)
