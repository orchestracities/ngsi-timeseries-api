import os
import pytest

QL_HOST = os.environ.get('QL_HOST', "quantumleap")
QL_PORT = 8668
QL_URL = "http://{}:{}".format(QL_HOST, QL_PORT)

CRATE_HOST = os.environ.get('CRATE_HOST', 'crate')
CRATE_PORT = 4200


def do_clean_crate():
    from crate import client
    conn = client.connect(["{}:{}".format(CRATE_HOST, CRATE_PORT)], error_trace=True)
    cursor = conn.cursor()

    try:
        cursor.execute("select table_name from information_schema.tables where table_schema = 'doc'")
        for tn in cursor.rows:
            cursor.execute("DROP TABLE IF EXISTS {}".format(tn[0]))
    finally:
        cursor.close()


@pytest.fixture()
def clean_crate():
    yield
    do_clean_crate()


@pytest.fixture
def entity():
    entity = {
        'id': 'Room1',
        'type': 'Room',
        'temperature': {
            'value': 24.2,
            'type': 'Number',
            'metadata': {}
        },
        'pressure': {
            'value': 720,
            'type': 'Number',
            'metadata': {}
        }
    }
    return entity
