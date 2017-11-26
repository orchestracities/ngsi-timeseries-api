"""
Script to create subscriptions for changes in entities of type
AirQualityObserved and TrafficFlowObserved to be sent to Comet.
"""
from __future__ import print_function
from experiments.dataModels.utils import HEADERS_PUT
import json
import os
import requests
import pprint

# INPUT (via environment variables)
COMET_URL = os.environ.get('COMET_URL', 'http://comet:8666')
ORION_URL = os.environ.get('ORION_URL', 'http://0.0.0.0:1026')


def create_subscription_v1(entity_type, notify_url):
    s = {
        "entities": [
            {
                "type": entity_type,
                "isPattern": "true",
                "id": ".*"
            }
        ],
        "attributes": [
        ],
        "reference": notify_url,
        "duration": "P1M",
        "notifyConditions": [
            {
                "type": "ONCHANGE",
                "condValues": [
                ]
            }
        ],
    }
    return s


def subscribe(entity_type):
    msg = "Subscribing at '{}', to notify to '{}' about any changes of '{}'"
    notify_url = '{}/notify'.format(COMET_URL)
    orion_url = '{}/v1/subscribeContext'.format(ORION_URL)
    print(msg.format(ORION_URL, notify_url, entity_type))

    subscription = create_subscription_v1(entity_type, notify_url)
    pprint.pprint(subscription)

    r = requests.post(orion_url, data=json.dumps(subscription),
                      headers=HEADERS_PUT)
    assert r.ok, r.text
    print("Subscription successfully created".format(ORION_URL, COMET_URL))


if __name__ == '__main__':
    subscribe('TrafficFlowObserved')
    print('\n')
    subscribe('AirQualityObserved')
