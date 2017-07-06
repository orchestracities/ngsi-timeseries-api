"""
Simple script to experiment with QuantumLeap (QL).

It will make the proper subscription in Orion and then create/update entities to generate the notifications for QL.
"""
from client.client import OrionClient
from client.fixtures import do_clean_mongo
from conftest import do_clean_crate
from experiments.comet.crazy_sensor import create_entity, update_args, sense
from translators.crate import CrateTranslator
from utils.hosts import LOCAL
import json

SLEEP = 5


def subscribe(orion, subscription):
    r = orion.subscribe(subscription)
    assert r.ok, r.text

    r = orion.get('subscriptions')
    assert r.ok
    assert r.status_code == 200

    subscription_id = json.loads(r.text)[0]
    return subscription_id


def get_subscription():
    from conftest import QL_URL
    entity_id = '.*'
    notify_url = '{}/notify'.format(QL_URL)
    subscription = {
        "description": "Test subscription",
        "subject": {
            "entities": [
              {
                "idPattern": entity_id,
                "type": "Room"
              }
            ],
            "condition": {
              "attrs": [
                "temperature",
              ]
            }
          },
        "notification": {
            "http": {
              "url": notify_url
            },
            "attrs": [
                "temperature",
            ],
            "metadata": ["dateCreated", "dateModified"]
        },
        "throttling": 5
    }
    return subscription


if __name__ == '__main__':
    orion = OrionClient(host=LOCAL)
    entity = create_entity('Room1')
    subscription = get_subscription()

    subscription_id = subscribe(orion, subscription)
    try:
        sense(orion, entity, update_args, SLEEP)
        pass
    finally:
        r = orion.unsubscribe(subscription_id)
        assert r.ok, r.text

        # Cleanup Orion
        do_clean_mongo()

        # Cleanup CrateDB
        do_clean_crate()
