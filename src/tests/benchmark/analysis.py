import pandas as pd

from server.telemetry.pandas_import import TelemetryDB, TelemetryFrame, \
    TelemetrySeries


def _describe(s: pd.Series):
    ps = [0.25, 0.5, 0.75, 0.9, 0.95]
    d = s.describe(percentiles=ps)
    print(d)


def print_series_summary(series: TelemetrySeries, by_pid: bool = False):
    if by_pid:
        for pid in sorted(series.pids()):
            pd_s = series.data(by_pid=pid)
            print(f"Time series: {series.label()} | PID {pid}")
            _describe(pd_s)
    else:
        pd_s = series.data()
        print(f"Time series: {series.label()}")
        _describe(pd_s)


def print_measurements_summaries(frame: TelemetryFrame, by_pid: bool = False):
    for label in sorted(frame.labels()):
        t = frame.time_series(label)
        print_series_summary(t, by_pid)
        print()


def measurements_per_second(series: TelemetrySeries) -> pd.Series:
    return series.data().resample('1S').count()


def sum_by_second_difference(t1: TelemetrySeries, t2: TelemetrySeries) \
        -> (float, pd.Series):
    # NB assumption: for each k . t1[k] <= t2[k]
    s1 = t1.data().sum()
    s2 = t2.data().sum()
    diff_ratio = (s2 - s1) / s2  # ~1% => s1 ~ s2; ~99% => s2 predominant

    x = t1.data().resample('1S').sum()  # sum values in each 1-second bucket
    y = t2.data().resample('1S').sum()
    return diff_ratio, y.sub(x)


def sum_by_second_ratio(t1: TelemetrySeries, t2: TelemetrySeries) \
        -> (float, pd.Series):
    s1 = t1.data().sum()
    s2 = t2.data().sum()
    ratio = s1 / s2

    x = t1.data().resample('1S').sum()  # sum values in each 1-second bucket
    y = t2.data().resample('1S').sum()
    return ratio, x.divide(y)           # result[k] = x[k] / y[k]


def plot_to_file(figure_name: str, data: pd.Series):
    fig = data.plot().get_figure()
    fig.savefig(f"{figure_name}.pdf")


db = TelemetryDB('_monitoring')

# print_measurements_summaries(db.duration())
# print_measurements_summaries(db.duration(), by_pid = True)
#
# print_series_summary(db.max_rss())
# print_series_summary(db.max_rss(), by_pid = True)
#
# db.duration().labels()
# get_version = db.duration().time_series('/version [GET]')
# rps = measurements_per_second(get_version)
# rps.describe()
# plot_to_file('get-version-rps', rps)
#
# version_fn = db.duration().time_series('version()')
# ratio, diff_series = sum_by_second_difference(version_fn, get_version)
# ratio, r_series = sum_by_second_ratio(db.user_time(), db.system_time())
