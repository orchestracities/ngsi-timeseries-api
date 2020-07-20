import pg8000

from translators.timescale import postgres_translator_instance, \
    PostgresConnectionData

from .original_data_scenarios import *


@pytest.fixture(scope='module')
def with_timescale():
    pg8000.paramstyle = "qmark"
    t = PostgresConnectionData()
    t.read_env()

    pg_conn = pg8000.connect(host=t.host, port=t.port,
                             database=t.db_name,
                             user=t.db_user, password=t.db_pass)
    pg_conn.autocommit = True
    pg_cursor = pg_conn.cursor()

    yield OriginalDataScenarios(postgres_translator_instance, pg_cursor)

    pg_cursor.close()
    pg_conn.close()


def test_changed_attr_type_scenario(with_timescale):
    with_timescale.run_changed_attr_type_scenario()


def test_inconsistent_attr_type_in_batch_scenario(with_timescale):
    with_timescale.run_inconsistent_attr_type_in_batch_scenario()


def test_data_loss_scenario(with_timescale):
    with_timescale.run_data_loss_scenario()


def test_success_scenario(with_timescale):
    with_timescale.run_success_scenario()


def test_success_scenario_with_keep_raw_on(with_timescale):
    with_timescale.run_success_scenario_with_keep_raw_on()


def test_query_failed_entities_scenario(with_timescale):
    with_timescale.run_query_failed_entities_scenario(
        fetch_batch_id_clause=f"({ORIGINAL_ENTITY_COL} ->> 'failedBatchID')"
    )
