from typing import Any

from server.telemetry.observation import ObservationBucket, observe, \
    observe_many
from utils.thread import BackgroundRepeater
from wq.core import QMan, WorkQ


class RowCountSampler(BackgroundRepeater):

    @staticmethod
    def count_label(table_fqn: str) -> str:
        return f"{table_fqn}:count"

    @staticmethod
    def delta_label(table_fqn: str) -> str:
        return f"{table_fqn}:count-delta"

    def __init__(self,
                 bucket: ObservationBucket,
                 db_connection: Any,
                 table_fqn: str,
                 max_rows: int,
                 sampling_interval: float = 1.0):
        super().__init__(sleep_interval=sampling_interval)
        self._bucket = bucket
        self._db_con = db_connection
        self._db = db_connection.cursor()
        self._table_fqn = table_fqn
        self._max_rows = max_rows
        self._current_rows = 0

    def _stop(self):
        self._bucket.empty()
        try:
            self._db_con.close()
        except BaseException:
            pass

    def _count_rows(self) -> int:
        try:
            stmt = f"select count(*) from {self._table_fqn}"
            self._db.execute(stmt)
            return self._db.fetchone()[0]
        except Exception as e:
            print(e)
            return 0

    def _observe(self, new_count: int, delta: int):
        x1 = (self.count_label(self._table_fqn), float(new_count))
        x2 = (self.delta_label(self._table_fqn), float(delta))
        xs = observe_many(x1, x2)
        self._bucket.put(*xs)

    def _do_run(self) -> bool:
        new_count = self._count_rows()
        if new_count > 0:
            delta = new_count - self._current_rows
            self._current_rows = new_count
            self._observe(new_count, delta)

        if self._current_rows >= self._max_rows:
            self._stop()
            return True

        return False

    def kill(self):
        super().kill()
        self._stop()


class WorkQSizeSampler(BackgroundRepeater):

    @staticmethod
    def size_label(q_name: str) -> str:
        return f"q:{q_name}:size"

    def __init__(self,
                 bucket: ObservationBucket,
                 q: WorkQ,
                 q_name: str,
                 sampling_interval: float = 1.0):
        super().__init__(sleep_interval=sampling_interval)
        self._bucket = bucket
        self._q_man = QMan(q)
        self._q_name = q_name

    def _do_run(self) -> bool:
        try:
            size = self._q_man.count_pending_tasks(task_id_prefix=None)
            label = self.size_label(self._q_name)
            self._bucket.put(observe(label, float(size)))
        except Exception as e:
            print(e)
        return False

    def _stop(self):
        self._bucket.empty()

    def kill(self):
        super().kill()
        self._stop()
