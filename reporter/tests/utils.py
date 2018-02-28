from client.client import HEADERS_PUT
from conftest import QL_URL
from datetime import datetime
import json
import requests


def notify_url():
    return "{}/notify".format(QL_URL)


def insert_test_data(translator, entity_types, n_entities, n_days):
    assert isinstance(entity_types, list)

    def get_notification(et, ei, temp_value, mod_value):
        return {
            'subscriptionId': '5947d174793fe6f7eb5e3961',
            'data': [
                {
                    'id': '{}{}'.format(et, ei),
                    'type': et,
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

    for et in entity_types:
        for ei in range(n_entities):
            for d in range(n_days):
                dt = datetime(1970, 1, d+1).isoformat()
                n = get_notification(et, ei, temp_value=d, mod_value=dt)
                r = requests.post(notify_url(),
                                  data=json.dumps(n),
                                  headers=HEADERS_PUT)
                assert r.ok

    translator._refresh(entity_types)
