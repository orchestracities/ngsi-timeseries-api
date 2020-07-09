from crate import client

from translators.crate import CrateTranslatorInstance
from utils.cfgreader import *

from .original_data_scenarios import *


@pytest.fixture(scope='module')
def with_crate():
    r = EnvReader(log=logging.getLogger(__name__).info)
    host = r.read(StrVar('CRATE_HOST', 'crate'))
    port = r.read(IntVar('CRATE_PORT', 4200))

    conn = client.connect([f"{host}:{port}"], error_trace=True)
    cursor = conn.cursor()

    yield OriginalDataScenarios(CrateTranslatorInstance, cursor,
                                delay_query_by=1)

    cursor.close()
    conn.close()


def test_changed_attr_type_scenario(with_crate):
    with_crate.run_changed_attr_type_scenario()


def test_inconsistent_attr_type_in_batch_scenario(with_crate):
    with_crate.run_inconsistent_attr_type_in_batch_scenario()


def test_data_loss_scenario(with_crate):
    with_crate.run_data_loss_scenario()


def test_success_scenario(with_crate):
    with_crate.run_success_scenario()


def test_success_scenario_with_keep_raw_on(with_crate):
    with_crate.run_success_scenario_with_keep_raw_on()


def test_query_failed_entities_scenario(with_crate):
    with_crate.run_query_failed_entities_scenario(
        fetch_batch_id_clause=f"{ORIGINAL_ENTITY_COL}['failedBatchID']"
    )
