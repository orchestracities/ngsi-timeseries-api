import pg8000
from crate import client

from translators.timescale import postgres_translator_instance, \
    PostgresConnectionData
from translators.crate import crate_translator_instance
from utils.cfgreader import *

from .original_data_scenarios import *

# To test a single translator use the -k parameter followed by either
# timescale or crate.
# See https://docs.pytest.org/en/stable/example/parametrize.html


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


@pytest.fixture(scope='module')
def with_crate():
    r = EnvReader(log=logging.getLogger(__name__).info)
    host = r.read(StrVar('CRATE_HOST', 'crate'))
    port = r.read(IntVar('CRATE_PORT', 4200))

    conn = client.connect([f"{host}:{port}"], error_trace=True)
    cursor = conn.cursor()

    yield OriginalDataScenarios(crate_translator_instance, cursor,
                                delay_query_by=1)

    cursor.close()
    conn.close()


translators = [
    pytest.lazy_fixture('with_timescale'),
    pytest.lazy_fixture('with_crate')
]


@pytest.mark.parametrize("translator", translators, ids=["timescale", "crate"])
def test_changed_attr_type_scenario(translator):
    translator.run_changed_attr_type_scenario()


@pytest.mark.parametrize("translator", translators, ids=["timescale", "crate"])
def test_inconsistent_attr_type_in_batch_scenario(translator):
    translator.run_inconsistent_attr_type_in_batch_scenario()


@pytest.mark.parametrize("translator", translators, ids=["timescale", "crate"])
def test_data_loss_scenario(translator):
    translator.run_data_loss_scenario()


@pytest.mark.parametrize("translator", translators, ids=["timescale", "crate"])
def test_success_scenario(translator):
    translator.run_success_scenario()


@pytest.mark.parametrize("translator", translators, ids=["timescale", "crate"])
def test_success_scenario_with_keep_raw_on(translator):
    translator.run_success_scenario_with_keep_raw_on()


@pytest.mark.parametrize("translator", translators, ids=["timescale", "crate"])
def test_query_failed_entities_scenario(translator):
    clause = f"({ORIGINAL_ENTITY_COL} ->> 'failedBatchID')"
    if translator.get_translator() == crate_translator_instance:
        clause = f"{ORIGINAL_ENTITY_COL}['failedBatchID']"

    translator.run_query_failed_entities_scenario(
        fetch_batch_id_clause=clause
    )
