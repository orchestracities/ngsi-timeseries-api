from client.client import HEADERS_PUT
from conftest import QL_URL
from datetime import datetime
import json
import requests


def notify_url():
    return "{}/notify".format(QL_URL)


def insert_test_data(translator, n_days, entity_type):
    def get_notification(temp_value, mod_value):
        return {
            'subscriptionId': '5947d174793fe6f7eb5e3961',
            'data': [
                {
                    'id': 'Room1',
                    'type': entity_type,
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
        r = requests.post('{}'.format(notify_url()),
                          data=json.dumps(n),
                          headers=HEADERS_PUT)
        assert r.ok

    translator._refresh([entity_type])
