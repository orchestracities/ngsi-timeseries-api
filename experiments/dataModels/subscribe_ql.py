"""
Script to create subscriptions for changes in entities of type AirQualityObserved and TrafficFlowObserved to be sent
to Quantumleap.
"""
from __future__ import print_function
import json
import os
import requests
import pprint

# INPUT (via environment variables)
QL_URL = os.environ.get('QL_URL', 'http://quantumleap:8668')
ORION_URL = os.environ.get('ORION_URL', 'http://0.0.0.0:1026')

# INTERNAL
HEADERS = {
    'Fiware-Service': 'default',
    'Fiware-ServicePath': '/',
}
HEADERS_PUT = HEADERS.copy()
HEADERS_PUT['Content-Type'] = 'application/json'


def subscribe(entity_type):
    notify_url = '{}/notify'.format(QL_URL)
    subscription = {
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
    orion_url = '{}/v2/subscriptions'.format(ORION_URL)

    print("Subscribing at '{}', to notify to '{}' about any changes of '{}'".format(ORION_URL, notify_url, entity_type))
    pprint.pprint(subscription)
    r = requests.post(orion_url, data=json.dumps(subscription), headers=HEADERS_PUT)
    assert r.ok, r.text
    print("Subscription successfully created".format(ORION_URL, QL_URL))


if __name__ == '__main__':
    subscribe('TrafficFlowObserved')
    print('\n')
    subscribe('AirQualityObserved')
