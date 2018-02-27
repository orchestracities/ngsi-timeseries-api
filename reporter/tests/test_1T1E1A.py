from client.client import HEADERS
from conftest import QL_URL
from reporter.tests.utils import insert_test_data
from translators.fixtures import crate_translator as translator
import requests


def query_url(entityId, attrName):
    return "{qlUrl}/entities/{entityId}/attrs/{attrName}".format(
        qlUrl=QL_URL,
        entityId=entityId,
        attrName=attrName,
    )


def test_1T1E1A_defaults(translator):
    n_days = 30
    entity_type = 'Room'
    insert_test_data(translator, n_days, entity_type)

    # Query
    query_params = {
        'type': entity_type,
    }
    r = requests.get(query_url('Room1', 'temperature'),
                     params=query_params,
                     headers=HEADERS)
    assert r.status_code == 200, r.text

    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in range(n_days)
    ]
    expected_values = list(range(n_days))
    expected_data = {
        'data': {
            'attrName': 'temperature',
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_values,
        }
    }
    assert r.json() == expected_data
