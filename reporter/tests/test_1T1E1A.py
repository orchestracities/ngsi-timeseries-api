from client.client import HEADERS, HEADERS_PUT
from conftest import QL_URL
from datetime import datetime
from translators.fixtures import crate_translator as translator
import json
import requests

notify_url = "{}/notify".format(QL_URL)


def insert_test_data(n_days):
    def get_notification(temp_value, mod_value):
        return {
            'subscriptionId': '5947d174793fe6f7eb5e3961',
            'data': [
                {
                    'id': 'Room1',
                    'type': 'Room',
                    'temperature': {
                        'type': 'Number',
                        'value': temp_value,
                        'metadata': {
                            'dateModified': {
                                'type': 'DateTime',
                                'value': mod_value
                            }
                        }
                    }
                }
            ]
        }

    for i in range(n_days):
        dt = datetime(1970, 1, i+1).isoformat()
        n = get_notification(temp_value=i, mod_value=dt)
        r = requests.post('{}'.format(notify_url),
                          data=json.dumps(n),
                          headers=HEADERS_PUT)
        assert r.ok


def test_1T1E1A_defaults(translator):
    # Prepare test data
    n_days = 30
    insert_test_data(n_days)
    translator._refresh(['Room'])

    # Query
    query_url = "{qlUrl}/entities/{entityId}/attrs/{attrName}".format(
        qlUrl=QL_URL,
        entityId='Room1',
        attrName='temperature',
    )
    entity_type = 'Room'
    query_params = {
        'type': entity_type,
    }

    r = requests.get('{}'.format(query_url), params=query_params,
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
