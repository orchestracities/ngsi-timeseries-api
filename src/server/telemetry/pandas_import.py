"""
Utilities to import CSV telemetry data into Pandas data frames and series.
"""

from glob import glob
import os
from typing import Optional

import pandas as pd

from server.telemetry.flush import TIMEPOINT_CSV_FIELD, MEASUREMENT_CSV_FIELD, \
    LABEL_CSV_FIELD, PID_CSV_FIELD
from server.telemetry.monitor import DURATION_FILE_PREFIX, RUNTIME_FILE_PREFIX
from server.telemetry.sampler import GC_COLLECTIONS, GC_COLLECTED, \
    GC_UNCOLLECTABLE, PROC_MAX_RSS, PROC_SYSTEM_TIME, PROC_USER_TIME


def _csv_file_pattern(monitoring_dir: str, file_prefix: str) -> str:
    return os.path.join(monitoring_dir, f"{file_prefix}*.csv")


def _duration_file_pattern(monitoring_dir: str) -> str:
    return _csv_file_pattern(monitoring_dir, DURATION_FILE_PREFIX)


def _runtime_file_pattern(monitoring_dir: str) -> str:
    return _csv_file_pattern(monitoring_dir, RUNTIME_FILE_PREFIX)


def _parse_csv(pathname: str) -> pd.DataFrame:
    def from_epoch_ns(t): return pd.to_datetime(int(t),
                                                unit='ns', origin='unix')
    converters = {
        TIMEPOINT_CSV_FIELD: from_epoch_ns
    }
    return pd.read_csv(pathname, converters=converters)


def _load_csv_files(pathname_pattern: str) -> pd.DataFrame:
    path_names = glob(pathname_pattern)
    frames = [_parse_csv(p) for p in path_names]
    return pd.concat(frames, ignore_index=True)


class TelemetrySeries:

    @staticmethod
    def form_telemetry_data(label: str, frame: pd.DataFrame) \
            -> 'TelemetrySeries':
        cols = [TIMEPOINT_CSV_FIELD, MEASUREMENT_CSV_FIELD, PID_CSV_FIELD]
        proj = frame[frame[LABEL_CSV_FIELD] == label][cols]
        time_indexed_data = proj.set_index(TIMEPOINT_CSV_FIELD)

        return TelemetrySeries(label, time_indexed_data)

    def __init__(self, label: str, data: pd.DataFrame):
        self._label = label
        self._pids = [pid for pid in data[PID_CSV_FIELD].unique()]
        self._data = data

    def label(self) -> str:
        """
        :return: this series' identifier.
        """
        return self._label

    def pids(self) -> [int]:
        """
        :return: the PIDs of the processes that produced the measurements
            in this series.
        """
        return self._pids

    def data(self, by_pid: Optional[int] = None) -> pd.Series:
        """
        Extract the telemetry ``ObservationSeries`` as a Pandas time series.

        :param by_pid: optional argument to extract only the data collected by
            the process having the given PID.
        :return: a Pandas time series with the observed measurements.
        """
        if by_pid:
            group = self._data[self._data['PID'] == by_pid]
            return group[MEASUREMENT_CSV_FIELD]
        else:
            return self._data[MEASUREMENT_CSV_FIELD]


class TelemetryFrame:
    """
    Holds a Pandas frame with telemetry data combined from CSV files.
    """

    def __init__(self, frame: pd.DataFrame):
        self._frame = frame
        self._labels = [lbl for lbl in frame[LABEL_CSV_FIELD].unique()]

    def labels(self) -> [str]:
        """
        :return: the label (unique name) of each series in the data set.
        """
        return self._labels

    def time_series(self, label: str) -> TelemetrySeries:
        """
        Extract the time series identified by the given label.

        :param label: the (unique) name of the series in the data set.
        :return: an object to access the series data.
        """
        return TelemetrySeries.form_telemetry_data(label, self._frame)


class TelemetryDB:
    """
    Convenience class to collect all duration and runtime telemetry data
    found in the monitoring directory and make the data query-able through
    Pandas frames and series.
    """

    @staticmethod
    def from_duration_data(monitoring_dir: str) -> 'TelemetryFrame':
        """
        Collect duration telemetry data into a Pandas frame.
        Import every duration CSV file in the specified monitoring directory
        into a Pandas frame and then join all the frames into one.

        :param monitoring_dir: the directory containing telemetry data.
        :return: the whole duration data set.
        """
        data = _load_csv_files(_duration_file_pattern(monitoring_dir))
        return TelemetryFrame(data)

    @staticmethod
    def from_runtime_data(monitoring_dir: str) -> 'TelemetryFrame':
        """
        Collect runtime telemetry data into a Pandas frame.
        Import every duration CSV file in the specified monitoring directory
        into a Pandas frame and then join all the frames into one.

        :param monitoring_dir: the directory containing telemetry data.
        :return: the whole runtime data set.
        """
        data = _load_csv_files(_runtime_file_pattern(monitoring_dir))
        return TelemetryFrame(data)

    def __init__(self, monitoring_dir: str):
        self._duration_frame = self.from_duration_data(monitoring_dir)
        self._runtime_frame = self.from_runtime_data(monitoring_dir)

    def duration(self) -> TelemetryFrame:
        return self._duration_frame

    def gc_collections(self) -> TelemetrySeries:
        return self._runtime_frame.time_series(GC_COLLECTIONS)

    def gc_collected(self) -> TelemetrySeries:
        return self._runtime_frame.time_series(GC_COLLECTED)

    def gc_uncollectable(self) -> TelemetrySeries:
        return self._runtime_frame.time_series(GC_UNCOLLECTABLE)

    def max_rss(self) -> TelemetrySeries:
        return self._runtime_frame.time_series(PROC_MAX_RSS)

    def system_time(self) -> TelemetrySeries:
        return self._runtime_frame.time_series(PROC_SYSTEM_TIME)

    def user_time(self) -> TelemetrySeries:
        return self._runtime_frame.time_series(PROC_USER_TIME)
