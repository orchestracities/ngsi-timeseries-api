import json
import os
import requests

# Input
QL_HOST = os.environ.get('QL_HOST', '0.0.0.0')
QL_PORT = os.environ.get('QL_PORT', '8668')
ORION_HOST = os.environ.get('ORION_HOST', '0.0.0.0')
ORION_PORT = os.environ.get('ORION_PORT', '1026')

# Internal
QL_URL = 'http://{}:{}'.format(QL_HOST, QL_PORT)
NOTIFY_URL = notify_url = '{}/v2/notify'.format(QL_URL)


def subscribe(entity_type):
    subscription = {
        "description": "Test subscription",
        "subject": {
            "entities": [
              {
                "idPattern": ".*",
                "type": entity_type
              }
            ],
            "condition": {
              "attrs": [
                "temperature",
                "pressure",
                "humidity",
              ]
            }
          },
        "notification": {
            "http": {
              "url": NOTIFY_URL
            },
            "attrs": [
                "temperature",
                "pressure",
                "humidity",
            ],
            "metadata": ["dateCreated", "dateModified"]
        },
        "throttling": 5
    }
    orion_url = 'http://{}:{}'.format(ORION_HOST, ORION_PORT)
    r = requests.post('{}/v2/subscriptions'.format(orion_url),
                      data=json.dumps(subscription),
                      headers={'Content-Type': 'application/json'})
    assert r.ok, r.text
    print('Subscription successfully finished:')
    print('Entity Type: {}'.format(entity_type))
    print('Notify URL: {}'.format(NOTIFY_URL))


if __name__ == '__main__':
    entity_type = 'WeatherStation'
    subscribe(entity_type)
