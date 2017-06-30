"""
Simple script to experiment with QuantumLeap (QL).

It will make the proper subscription in Orion and then create/update entities to generate the notifications for QL.
"""
import json

from client.client import OrionClient
from experiments.comet.crazy_sensor import create_entity, update_args, sense
from translators.crate import CrateTranslator
from utils.hosts import LOCAL

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
    entity_id = '.*'
    notify_url = 'http://quantumleap:8668/notify'
    # notify_url = 'http://192.0.0.1:8668/notify'
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
    finally:
        r = orion.unsubscribe(subscription_id)
        assert r.ok, r.text

        # Cleanup CrateDB
        client = CrateTranslator(LOCAL)
        client.setup()
        client.dispose(testing=True)

