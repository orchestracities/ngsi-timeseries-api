"""
Simple script to experiment with QuantumLeap (QL).

It will make the proper subscription in Orion and then create/update entities to generate the notifications for QL.
"""
from client.client import OrionClient
from client.fixtures import do_clean_mongo
from conftest import do_clean_crate
from experiments.common import sense, subscribe
from experiments.comet.crazy_sensor import create_entity, update_args
from utils.hosts import LOCAL

SLEEP = 5


def get_subscription():
    from conftest import QL_URL
    notify_url = '{}/notify'.format(QL_URL)
    subscription = {
        "description": "Test subscription",
        "subject": {
            "entities": [
              {
                "idPattern": '.*',
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
    subscription = get_subscription()
    subscription_id = subscribe(orion, subscription)

    entity = create_entity('Room1')
    try:
        sense(orion, entity, update_args, SLEEP)
    finally:
        try:
            r = orion.delete(entity['id'])
            r = orion.unsubscribe(subscription_id)
        finally:
            # Cleanup Orion
            do_clean_mongo()

            # Cleanup CrateDB
            do_clean_crate()
