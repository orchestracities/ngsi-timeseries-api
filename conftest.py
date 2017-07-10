from translators.crate import CrateTranslator
import os
import pytest

QL_HOST = os.environ.get('QL_URL', "quantumleap")
QL_PORT = 8668
QL_URL = "http://{}:{}".format(QL_HOST, QL_PORT)

CRATE_HOST = os.environ.get('CRATE_HOST', 'crate')
CRATE_PORT = 4200


def do_clean_crate():
    from crate import client
    conn = client.connect(["{}:{}".format(CRATE_HOST, CRATE_PORT)], error_trace=True)
    cursor = conn.cursor()
    # For now, we're working with only one table.
    cursor.execute("DROP TABLE IF EXISTS {}".format(CrateTranslator.TABLE_NAME))


@pytest.fixture()
def clean_crate():
    yield
    do_clean_crate()
