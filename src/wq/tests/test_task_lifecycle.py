from time import sleep

from translators.timescale import postgres_translator_instance
from wq.core import QMan
from wq.ql.notify import InsertAction
from wq.tests.conftest import stop_timescale, start_timescale, \
    wait_for_timescale


FIWARE_SVC = 'x'

ENTITY = {
    "id": "Room:1",
    "type": "Room",
    "pressure": {
        "value": 720,
        "type": "Integer"
    }
}

DB_TABLE_FQN = 'mtx.etroom'


def count_db_entities(service_path: str) -> int:
    with postgres_translator_instance() as t:
        stmt = f"select count(*) from {DB_TABLE_FQN} where " + \
               f"fiware_servicepath = '{service_path}'"
        t.cursor.execute(stmt)
        return t.cursor.fetchone()[0]


def test_success():
    wait_for_timescale()

    svc_path = '/success'
    task = InsertAction(fiware_service=FIWARE_SVC,
                        fiware_service_path=svc_path,
                        fiware_correlation_id=None,
                        payload=[ENTITY])
    task.enqueue()

    sleep(2.0)

    db_count = count_db_entities(svc_path)
    assert db_count == 1

    qman = QMan(task.work_queue())
    q_count = qman.count_successful_tasks(None)
    assert q_count == 1


def test_failure():
    stop_timescale()
    try:
        svc_path = '/failure'
        task = InsertAction(fiware_service=FIWARE_SVC,
                            fiware_service_path=svc_path,
                            fiware_correlation_id=None,
                            payload=[ENTITY])
        task.enqueue()

        sleep(2.0)

        qman = QMan(task.work_queue())
        q_count = qman.count_failed_tasks(None)
        assert q_count == 1
    finally:
        start_timescale()


# TODO this one keeps on failing figure out how to get it right.
def test_retry():
    stop_timescale()
    restart_timescale = True
    try:
        svc_path = '/retry'
        task = InsertAction(fiware_service=FIWARE_SVC,
                            fiware_service_path=svc_path,
                            fiware_correlation_id=None,
                            payload=[ENTITY],
                            retry_intervals=[1, 10])
        task.enqueue()

        # qman = QMan(task.work_queue())
        # pending = qman.count_pending_tasks(None)
        # assert pending == 1

        start_timescale()
        wait_for_timescale(max_wait=5.0)
        restart_timescale = False

        sleep(10.0)

        db_count = count_db_entities(svc_path)
        assert db_count == 1
    finally:
        if restart_timescale:
            start_timescale()
