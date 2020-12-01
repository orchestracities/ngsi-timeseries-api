from glob import glob
import json
from threading import Lock
import statistics as stats
from sys import stdout
import time
from typing import Callable, Dict, List, Optional
from uuid import uuid4


#
# TODO consider alternatives
# This is a quick & dirty solution to start getting some performance data.
# Consider spending some time researching monitoring frameworks. Also if
# we do roll out our own thingie in the end, we should still probably use
# something like Pandas for data analysis.
#

class DurationStats:
    """
    Convenience class to compute some basic stats on a list of durations.
    """

    def __init__(self, samples: [float] = ()):
        self._samples = samples if samples else []

    def size(self) -> int:
        return len(self._samples)

    def _with_samples(self, compute: Callable[[List[float]], float],
                      min_len: int = 1) -> Optional[float]:
        if len(self._samples) >= min_len:
            return compute(self._samples)
        return None

    def min(self) -> Optional[float]:
        return self._with_samples(min)

    def max(self) -> Optional[float]:
        return self._with_samples(max)

    def mean(self) -> Optional[float]:
        return self._with_samples(stats.mean)

    def mode(self) -> Optional[float]:
        return self._with_samples(stats.mode)

    def median(self) -> Optional[float]:
        return self._with_samples(stats.median)

    def p90(self) -> Optional[float]:
        return self._with_samples(
            lambda xs: stats.quantiles(xs, n=100, method='inclusive')[-1],
            min_len=2
        )
        # TODO is this actually computing the 90th percentile?

    def __str__(self):
        def stringify(fn: Callable[[], Optional[float]]) -> str:
            result = fn()
            if result is not None:
                return f"{int(result * 1000)}ms"
            return 'n/a'

        xs = [
            f"size: {self.size()}",
            f"min: {stringify(self.min)}",
            f"max: {stringify(self.max)}",
            f"mean: {stringify(self.mean)}",
            f"median: {stringify(self.median)}",
            f"mode: {stringify(self.mode)}",
            f"p90: {stringify(self.p90)}"
        ]
        return '\t'.join(xs)


class DurationTable:
    """
    Stores lists of durations, each list being identified by a key.
    """

    @staticmethod
    def _merge_tables(table_dicts: [Dict[str, List[float]]]) -> 'DurationTable':
        merged = {}
        for t in table_dicts:  # TODO implement efficient merge algo
            for k in t:
                ds = merged.get(k, [])
                ds.extend(t[k])
                merged[k] = ds

        table = DurationTable()
        table._data = merged
        return table

    @staticmethod
    def from_files(pathname_pattern: str) -> 'DurationTable':
        """
        Aggregate duration data from files into a single DurationTable.
        Each file is supposed to be a JSON dict where keys are strings
        and values are lists of floats. Lists keyed by the same key get
        joined together.

        :param pathname_pattern: glob to collect files, e.g. '/tmp/data*.json'
        :return: a DurationTable with all the data read from the files matched
            by the given glob.
        """
        path_names = glob(pathname_pattern)
        table_dicts = []
        for p in path_names:
            with open(p, 'r') as infile:
                data = json.load(infile)
                table_dicts.append(data)

        return DurationTable._merge_tables(table_dicts)

    def __init__(self):
        self._data = {}

    def records(self) -> Dict[str, List[float]]:
        """
        :return: a dictionary where durations lists are keyed by their
            respective identifiers.
        """
        return self._data

    def insert(self, key: str, duration: float):
        """
        Append the input duration to the list keyed by the given key.

        :param key: identifies a duration list.
        :param duration: the sample to append.
        """
        ds = self._data.get(key, [])
        ds.append(duration)
        self._data[key] = ds

    def stats(self) -> Dict[str, DurationStats]:
        """
        :return: the collected samples wrapped by DurationStats for easy
            stats calculation.
        """
        return {
            k: DurationStats(samples)
            for (k, samples) in self._data.items()
        }

    def print_stats(self, fd=stdout):
        """
        Print statistics for each duration list on stdout.

        :param fd: specify a stream other than the default stdout.
        """
        for (k, ds) in self.stats().items():
            print(f"{k}\n\t{ds}\n", file=fd)

    def write_stats(self, pathname: str):
        """
        Write statistics for each duration list to file, overwriting any
        existing file at the same location.

        :param pathname: path to the file to write.
        """
        with open(pathname, 'w') as outfile:
            self.print_stats(fd=outfile)


class Timer:
    """
    Thread-safe timer.
    """

    def __init__(self):
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
        self._timers[timer_id] = time.perf_counter()
        # TODO rather use perf_counter_ns()?

        return timer_id

    def stop(self, timer_id) -> float:
        """
        Stop a previously started timer and compute how much time has elapsed
        since starting it.

        :param timer_id: the timer ID returned by the start call.
        :return: time elapsed, in fractional seconds, from the start call.
        """
        duration = time.perf_counter() - self._timers.pop(timer_id)
        return duration
        # NOTE. pop gets rid of the timer to keep memory footprint small


class DurationSampler:
    """
    Samples durations, storing them in a DurationTable.
    Thread-safe.
    """

    def __init__(self):
        self._data = DurationTable()
        self._timer = Timer()
        self._lock = Lock()

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

        :param key: identifies the list of durations where the current sample
            should be added.
        :param sample_id: the sample ID as returned by the sample method when
            the sample was started.
        """
        duration = self._timer.stop(sample_id)
        with self._lock:                      # (1)
            self._data.insert(key, duration)  # (2)
        # NOTES.
        # 1. Locking. It shouldn't affect performance adversely since typically
        # collect gets called after servicing the HTTP request. Also if threads
        # compete for the lock, that time won't be reflected in the samples.
        # 2. Memory footprint. According to the interwebs, it isn't really worth
        # your while pre-allocating a list with an initial capacity. I have
        # my doubts about this though and the effect of append on GC---i.e.
        # what if the list grows in too small chunks?
        #
        # TODO figure out to what extent (2) affects GC and how to optimise.

    def dump(self, pathname: str):
        """
        Write the collected samples to file as a JSON dictionary.
        Overwrite, if the file exists. Only call this method at the very
        end of the sampling session since it could have an impact on the
        sampling process otherwise.

        :param pathname: the path to the file to write.
        """
        with open(pathname, 'w') as outfile:
            json.dump(self._data.records(), outfile)
