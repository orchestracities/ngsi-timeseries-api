import pg8000
from time import sleep

from wq.core.mgmt import TaskStatus, TaskInfo
from wq.ql.notify import InsertAction, insert_task_finder
from wq.tests.conftest import pause_wq, resume_wq


PG_SU_NAME = 'postgres'
PG_SU_PASS = '*'

QL_DB_NAME = 'quantumleap'
QL_DB_USER = 'quantumleap'
QL_DB_PASS = '*'


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


def run_as_pg_su(stmt: str):
    conn = pg8000.connect(user=PG_SU_NAME, password=PG_SU_PASS)
    conn.autocommit = True
    with conn.cursor() as cursor:
        cursor.execute(stmt)


def close_pg_client_connections():
    stmt = 'select pg_terminate_backend(pid) from pg_stat_activity ' + \
           f"where datname = '{QL_DB_NAME}' and usename = '{QL_DB_USER}';"
    run_as_pg_su(stmt)


def disable_pg_connections():
    stmt = 'update pg_database set datallowconn = false ' + \
           f"where datname = '{QL_DB_NAME}';"
    run_as_pg_su(stmt)


def enable_pg_connections():
    stmt = 'update pg_database set datallowconn = true ' + \
           f"where datname = '{QL_DB_NAME}';"
    run_as_pg_su(stmt)


def count_db_entities(service_path: str) -> int:
    conn = pg8000.connect(database=QL_DB_NAME,
                          user=QL_DB_USER, password=QL_DB_PASS)
    conn.autocommit = True
    with conn.cursor() as cursor:
        stmt = f"select count(*) from {DB_TABLE_FQN} where " + \
               f"fiware_servicepath = '{service_path}'"
        cursor.execute(stmt)
        return cursor.fetchone()[0]


def enqueue_entity(svc_path: str, delay_after=3.0,
                   retry_intervals: [int] = None) -> InsertAction:
    task = InsertAction(fiware_service=FIWARE_SVC,
                        fiware_service_path=svc_path,
                        fiware_correlation_id=None,
                        payload=[ENTITY],
                        retry_intervals=retry_intervals)
    task.enqueue()
    sleep(delay_after)

    return task


def list_insert_tasks(id_prefix: str, state: TaskStatus) -> [TaskInfo]:
    find_tasks = insert_task_finder(state.value)
    ts = find_tasks(id_prefix)
    return list(ts)


def assert_task_final_q_state(task: InsertAction, expected_state: TaskStatus):
    id_prefix = task.task_id().fiware_svc_and_svc_path_repr()
    ts = list_insert_tasks(id_prefix, expected_state)

    assert len(ts) == 1

    task_info = ts[0]
    assert task_info.runtime.task_id == task.task_id().id_repr()


def assert_task_not_in_q_state(task: InsertAction, state: TaskStatus):
    id_prefix = task.task_id().fiware_svc_and_svc_path_repr()
    ts = list_insert_tasks(id_prefix, state)

    assert len(ts) == 0


def test_success():
    # put a task on the q and wait a couple of secs to make sure wq gets
    # to it.
    svc_path = '/success'
    task = enqueue_entity(svc_path)

    # the task's entity should be in the db now...
    db_count = count_db_entities(svc_path)
    assert db_count == 1

    # ...and the task should've transitioned to a final state of success.
    assert_task_final_q_state(task, TaskStatus.SUCCEEDED)


def test_failure():
    try:
        # insert one entity to make sure we've got a db table and wq has a
        # live connection to the db.
        enqueue_entity(svc_path='/ignore')

        # suspend the wq container, kill its db connection in postgres, and
        # stop postgres from accepting new connections.
        pause_wq()
        close_pg_client_connections()
        disable_pg_connections()

        # resume wq. the connection data it has in memory is no longer valid
        # and postgres won't let wq acquire a fresh connection.
        resume_wq()

        # when wq gets to process the entity below, the insert will fail b/c
        # it can't connect to the db...
        svc_path = '/failure'
        task = enqueue_entity(svc_path)

        # ...so there should be no entity in the db.
        enable_pg_connections()
        db_count = count_db_entities(svc_path)
        assert db_count == 0

        # the task should go in the failed lot.
        assert_task_final_q_state(task, TaskStatus.FAILED)

    finally:
        enable_pg_connections()


def test_retry():
    try:
        # kill any open wq connection in postgres and stop postgres from
        # accepting new connections.
        close_pg_client_connections()
        disable_pg_connections()

        # put an insert task on the q w/ 10 retries spaced out by 1 sec.
        # wait a couple of secs to make sure wq attempts to run the task
        # at least once.
        svc_path = '/retry'
        task = enqueue_entity(svc_path, retry_intervals=[1] * 10)

        # up until now, all wq's attempts to run the task should've failed
        # b/c wq can't connect to the db.
        assert_task_not_in_q_state(task, TaskStatus.SUCCEEDED)

        # make postgres accept new connections.
        # the next task try will fail again b/c the cached connection is still
        # unusable, but this time when the translator tries to recover from
        # the insert exception, it'll be able to acquire a fresh connection
        # to the db. So the retry following this should succeed.
        enable_pg_connections()

        # wait long enough for wq to retry the task at least twice.
        sleep(4)

        # now the entity should be in the db...
        db_count = count_db_entities(svc_path)
        assert db_count == 1

        # ...and the task should've transitioned to a final state of success.
        assert_task_final_q_state(task, TaskStatus.SUCCEEDED)
    finally:
        enable_pg_connections()
