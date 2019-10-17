from conftest import QL_URL
from datetime import datetime, timedelta
import json
import requests
import time


def notify_url():
    return "{}/v2/notify".format(QL_URL)


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


def insert_test_data(translator, entity_types, n_entities=1, index_size=30,
                     entity_id=None, index_base=None, index_period="day"):
    assert isinstance(entity_types, list)
    index_base = index_base or datetime(1970, 1, 1, 0, 0, 0, 0)

    for et in entity_types:
        for ei in range(n_entities):
            for i in range(index_size):
                if index_period == "year":
                    d = timedelta(days=365*i)
                elif index_period == "month":
                    d = timedelta(days=31*i)
                elif index_period == "day":
                    d = timedelta(days=i)
                elif index_period == "hour":
                    d = timedelta(hours=i)
                elif index_period == "minute":
                    d = timedelta(minutes=i)
                elif index_period == "second":
                    d = timedelta(seconds=i)
                else:
                    assert index_period == "milli"
                    d = timedelta(milliseconds=i)
                dt = index_base + d
                dt = dt.isoformat(timespec='milliseconds')

                eid = entity_id or '{}{}'.format(et, ei)
                n = get_notification(et, eid, attr_value=i, mod_value=dt)
                send_notifications([n])

    translator._refresh(entity_types)
