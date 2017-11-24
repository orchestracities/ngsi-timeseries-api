"""
Script to create subscriptions for changes in entities of type
AirQualityObserved and TrafficFlowObserved to be sent to Quantumleap.
"""
from __future__ import print_function
from experiments.dataModels.utils import HEADERS_PUT
import json
import os
import requests
import pprint

# INPUT (via environment variables)
QL_URL = os.environ.get('QL_URL', 'http://quantumleap:8668')
ORION_URL = os.environ.get('ORION_URL', 'http://0.0.0.0:1026')


def create_subscription(entity_type, notify_url):
    s = {
        "description": "traffic_flow_observed",
        "subject": {
            "entities": [
              {
                "idPattern": ".*",
                "type": entity_type
              }
            ],
            "condition": {
              "attrs": [
              ]
            }
          },
        "notification": {
            "http": {
              "url": notify_url
            },
            "attrs": [
            ],
            "metadata": ["dateCreated", "dateModified"]
        },
    }
    return s


def subscribe(entity_type):
    msg = "Subscribing at '{}', to notify to '{}' about any changes of '{}'"
    notify_url = '{}/notify'.format(QL_URL)
    orion_url = '{}/v2/subscriptions'.format(ORION_URL)
    print(msg.format(ORION_URL, notify_url, entity_type))

    subscription = create_subscription(entity_type, notify_url)
    pprint.pprint(subscription)

    r = requests.post(orion_url, data=json.dumps(subscription),
                      headers=HEADERS_PUT)
    assert r.ok, r.text
    print("Subscription successfully created".format(ORION_URL, QL_URL))


if __name__ == '__main__':
    subscribe('TrafficFlowObserved')
    print('\n')
    subscribe('AirQualityObserved')
