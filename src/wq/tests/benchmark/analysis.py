from server.telemetry.pandas_import import TelemetryDB, TelemetrySeries
from wq.core.cfg import default_queue_name
from tests.benchmark.pdutils import *
from wq.tests.benchmark.driver import TestScript, DB_TABLE_FQN
from wq.tests.benchmark.factory import GAUGE_FILE_PREFIX
from wq.tests.benchmark.samplers import RowCountSampler, WorkQSizeSampler


class Db(TelemetryDB):

    def __init__(self):
        mon_dir = TestScript.default_monitoring_dir()
        super().__init__(mon_dir)
        self._gauge_frame = self.from_csv_files(mon_dir, GAUGE_FILE_PREFIX)

    def queue_size(self) -> TelemetrySeries:
        """
        :return: number of messages on the queue over time (sampling interval:
            1 second)
        """
        label = WorkQSizeSampler.size_label(default_queue_name())
        return self._gauge_frame.time_series(label)

    def insert_count(self) -> TelemetrySeries:
        """
        :return: number of rows in the DB table over time (sampling interval:
            1 second)
        """
        label = RowCountSampler.count_label(DB_TABLE_FQN)
        return self._gauge_frame.time_series(label)

    def insert_delta(self) -> TelemetrySeries:
        """
        :return: number of new rows inserted in the DB table over time
            (sampling interval:1 second). For each time point in the
            series, the corresponding value is the number of rows that
            got inserted since the previous time point. So looking at
            this time series gives you a rough indication of overall
            system throughput.
        """
        label = RowCountSampler.delta_label(DB_TABLE_FQN)
        return self._gauge_frame.time_series(label)

    def insert_action(self) -> TelemetrySeries:
        """
        :return: total duration of each insert task executed by the work queue.
            Each duration is the time elapsed since the task got fetched from
            the queue until execution competes. It's the sum of the time taken
            to fetch the task from the queue, fork a worker process to run it,
            actually running the code to do the DB insert, and finally doing
            some queue bookkeeping to manage the task life-cycle.
        """
        label = "task: <class 'wq.ql.notify.InsertAction'>"
        return self.duration().time_series(label)

    def notify_post(self) -> TelemetrySeries:
        """
        :return: duration of each notify POST request handled by the QL front
        end. Notice if you configure QL not to use a work queue, then each
        duration will also include the time taken to run the DB insert.
        Otherwise it's just the time take to add a task to the work queue.
        """
        label = '/v2/notify [POST]'
        return self.duration().time_series(label)

    def client_notify(self) -> TelemetrySeries:
        """
        :return: duration of each successful client call to the notify endpoint.
        """
        label = "client:notify:200"
        return self.duration().time_series(label)


db = Db()

# print_series_summary(db.queue_size())
# print_series_summary(db.insert_count())
# print_series_summary(db.insert_delta())

# db.queue_size().data().plot()
# db.insert_count().data().plot()
# db.insert_delta().data().plot()

# print_series_summary(db.insert_action())
# rps = measurements_per_second(db.insert_action())
# rps.plot()
# rps.describe()

# print_series_summary(db.client_notify())
# rps = measurements_per_second(db.client_notify())
# rps.plot()
# rps.describe()

# print_series_summary(db.notify_post())
# rps = measurements_per_second(db.notify_post())
# rps.plot()
# rps.describe()
