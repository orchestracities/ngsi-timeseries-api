from conftest import QL_URL
from datetime import datetime
import json
import requests
import time


def notify_url():
    return "{}/notify".format(QL_URL)


def get_notification(et, ei, attr_value, mod_value):
    return {
        'subscriptionId': '5947d174793fe6f7eb5e3961',
        'data': [
            {
                'id': ei,
                'type': et,
                'temperature': {
                    'type': 'Number',
                    'value': attr_value,
                    'metadata': {
                        'dateModified': {
                            'type': 'DateTime',
                            'value': mod_value
                        }
                    }
                },
                'pressure': {
                    'type': 'Number',
                    'value': 10 * attr_value,
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


def send_notifications(notifications):
    assert isinstance(notifications, list)
    for n in notifications:
        h = {'Content-Type': 'application/json'}
        r = requests.post(notify_url(), data=json.dumps(n), headers=h)
        assert r.ok


def insert_test_data(translator, entity_types, n_entities, n_days,
                     entity_id=None):
    assert isinstance(entity_types, list)

    for et in entity_types:
        for ei in range(n_entities):
            for d in range(n_days):
                dt = datetime(1970, 1, d+1).isoformat(timespec='milliseconds')
                eid = entity_id or '{}{}'.format(et, ei)
                n = get_notification(et, eid, attr_value=d, mod_value=dt)
                send_notifications([n])

    translator._refresh(entity_types)
