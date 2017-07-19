from client.client import OrionClient
import os

# Input
QL_HOST = os.environ.get('QL_HOST', '0.0.0.0')
QL_PORT = os.environ.get('QL_PORT', '8668')
ORION_HOST = os.environ.get('ORION_HOST', '0.0.0.0')
ORION_PORT = os.environ.get('ORION_PORT', '1026')

# Internal
QL_URL = 'http://{}:{}'.format(QL_HOST, QL_PORT)
NOTIFY_URL = notify_url = '{}/notify'.format(QL_URL)


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
    orion = OrionClient(ORION_HOST, ORION_PORT)
    r = orion.subscribe(subscription)
    assert r.ok, r.text
    print('Subscription successfully finished:')
    print('Entity Type: {}'.format(entity_type))
    print('Notify URL: {}'.format(NOTIFY_URL))


if __name__ == '__main__':
    entity_type = 'WeatherStation'
    subscribe(entity_type)
