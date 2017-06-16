"""
Simple script that:
    - Connects to local Orion
    - Creates a Room entity
    - Updates its temperature with random values every SLEEP seconds.

Notifications are sent to NOTIFY_URL
"""
from client.client import OrionClient
from random import random
from utils.hosts import LOCAL
import json
import time


SLEEP = 5
ENTITY_ID = 'Room1'
NOTIFY_URL = 'http://comet:8666'


def subscribe(orion, url):
    r = orion.subscribe_v1('{}/notify'.format(url))
    assert r.ok, r.text

    data = json.loads(r.text)
    subscription_id = data['subscribeResponse']['subscriptionId']
    return subscription_id


def create_entity(entity_id):
    entity = {
        'id': entity_id,
        'type': 'Room',
        'temperature': {
            'value': 23,
            'type': 'Float'
        },
    }
    print('Entity: {}'.format(entity))
    return entity


def loop(orion, entity_id):
    try:
        while True:
            v = 10 + 30 * random()
            r = orion.update(entity_id, {'temperature': {'value': v, 'type': 'Float'}})
            print('Update to {:.2f}: {} {}'.format(v, r.status_code, r.text))
            time.sleep(SLEEP)
    finally:
        r = orion.delete(entity_id)
        assert r.ok, r.text
        r = orion.unsubscribe(subscription_id)
        assert r.ok, r.text


if __name__ == '__main__':
    orion = OrionClient(host=LOCAL)

    subscription_id = subscribe(orion, NOTIFY_URL)

    entity = create_entity(ENTITY_ID)

    r = orion.insert(entity)
    assert r.ok, r.text
    print('Insert: {} {}'.format(r.status_code, r.text))

    loop(orion, entity['id'])

