from pathlib import Path

from server.telemetry.pandas_import import TelemetryDB
from tests.benchmark.pdutils import *


db = TelemetryDB(Path('_monitoring'))

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
