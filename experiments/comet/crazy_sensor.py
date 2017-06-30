"""
Simple script that:
    - Connects to local Orion
    - Creates a Room entity
    - Updates its temperature with random values every SLEEP seconds.

Notifications are sent to NOTIFY_URL
"""
from client.client import OrionClient
from random import random
from utils.common import create_simple_subscription_v1
from utils.hosts import LOCAL
import json
import time


SLEEP = 5
ENTITY_ID = 'Room1'
NOTIFY_URL = 'http://comet:8666/notify'


def subscribe(orion, subscription):
    # v2 subscriptions are not returning the generated subscription id :s
    r = orion.subscribe_v1(subscription)
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
            'type': 'Number'
        },
    }
    return entity


def update_args():
    v = 10 + 30 * random()
    res = {'temperature': {'value': v, 'type': 'Number'}}
    return res


def sense(orion, entity, update_callback, sleep):
    r = orion.insert(entity)
    assert r.ok, r.text
    print('Inserted: {}'.format(entity))

    try:
        while True:
            time.sleep(sleep)
            args = update_callback()
            r = orion.update(entity['id'], args)
            assert r.ok, r.text
            print('Updated: {}'.format(args))

    finally:
        r = orion.delete(entity['id'])
        assert r.ok, r.text


if __name__ == '__main__':
    entity = create_entity(ENTITY_ID)
    subscription = create_simple_subscription_v1(NOTIFY_URL)

    orion = OrionClient(host=LOCAL)
    subscription_id = subscribe(orion, subscription)
    try:
        sense(entity, update_args, SLEEP)
    finally:
        r = orion.unsubscribe(subscription_id)
        assert r.ok, r.text

