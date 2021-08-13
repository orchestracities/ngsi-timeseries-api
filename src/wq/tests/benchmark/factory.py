from enum import Enum
from pathlib import Path
from typing import Any

from crate import client
import pg8000
from rq import Queue

from server.telemetry.monitor import _new_bucket
from translators.timescale import PostgresConnectionData
from utils.cfgreader import EnvReader, IntVar, StrVar
from wq.core.cfg import redis_connection, default_queue_name
from wq.tests.benchmark.samplers import RowCountSampler, WorkQSizeSampler


GAUGE_FILE_PREFIX = 'gauge'


class DbType(Enum):
    CRATE = 'crate'
    TIMESCALE = 'timescale'


def db_con_factory(t: DbType) -> Any:
    if t is DbType.CRATE:
        r = EnvReader()
        host = r.read(StrVar('CRATE_HOST', 'localhost'))
        port = r.read(IntVar('CRATE_PORT', 4200))

        return client.connect([f"{host}:{port}"], error_trace=True)
    if t is DbType.TIMESCALE:
        cfg = PostgresConnectionData()
        cfg.read_env()

        pg8000.paramstyle = "qmark"
        cx = pg8000.connect(host=cfg.host, port=cfg.port,
                            database=cfg.db_name,
                            user=cfg.db_user, password=cfg.db_pass)
        cx.autocommit = True

        return cx

    return None


def new_row_count_sampler(monitoring_dir: Path,
                          db_type: DbType,
                          table_fqn: str,
                          max_rows: int) -> RowCountSampler:
    con = db_con_factory(db_type)
    bucket = _new_bucket(str(monitoring_dir), GAUGE_FILE_PREFIX)
    return RowCountSampler(bucket=bucket, db_connection=con,
                           table_fqn=table_fqn, max_rows=max_rows)


def new_work_q_size_sampler(monitoring_dir: Path) -> WorkQSizeSampler:
    q_name = default_queue_name()
    q = Queue(q_name, connection=redis_connection())
    bucket = _new_bucket(str(monitoring_dir), GAUGE_FILE_PREFIX)
    return WorkQSizeSampler(bucket=bucket, q=q, q_name=q_name)
