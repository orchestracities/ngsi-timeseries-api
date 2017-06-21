from client.client import OrionClient, HEADERS_PUT
from client.fixtures import entity
from reporter.reporter import PORT as REPORTER_PORT
from translators.crate import CrateTranslator
import json
import pytest
import requests

# Loop-back alias, to ease local dev until having custom docker image.
# Required so that containerized orion can send notification to server running in local host.
LOCAL = '192.0.0.1'

# TODO: use pytest-flask for server instance of reporter (with CrateTranslator)
notify_url = "http://{}:{}/notify".format(LOCAL, REPORTER_PORT)


@pytest.fixture
def notification():
    return {
        'subscriptionId': '5947d174793fe6f7eb5e3961',
        'data': [
            {
                'id': 'Room1',
                'type': 'Room',
                'temperature': {
                    'type': 'Float',
                    'value': 25.4,
                    'metadata': {'dateModified': {'type': 'DateTime', 'value': '2017-06-19T11:46:45.00Z'}}}
            }
        ]
    }


def test_valid_notification(notification):
    r = requests.post('{}'.format(notify_url), data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 200
    assert r.text == 'Notification successfully processed'


def test_invalid_no_type(notification):
    notification['data'][0].pop('type')
    r = requests.post('{}'.format(notify_url), data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 400
    assert r.text == 'Entity type is required in notifications'


def test_invalid_no_id(notification):
    notification['data'][0].pop('id')
    r = requests.post('{}'.format(notify_url), data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 400
    assert r.text == 'Entity id is required in notifications'


def test_invalid_no_attr(notification):
    notification['data'][0].pop('temperature')
    r = requests.post('{}'.format(notify_url), data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 400
    assert r.text == 'Received notification without attributes other than "type" and "id"'


def test_invalid_no_modified(notification):
    notification['data'][0]['temperature']['metadata'].pop('dateModified')
    r = requests.post('{}'.format(notify_url), data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 400
    assert r.text == 'Modified attributes must come with dateModified metadata. ' \
                     'Include "metadata": [ "dateModified" ] in your notification params.'


def test_with_orion(entity):
    orion = OrionClient(host=LOCAL)

    entity_id = "Room1"
    subscription = {
        "description": "Test subscription",
        "subject": {
            "entities": [
              {
                "id": entity_id,
                "type": "Room"
              }
            ],
            "condition": {
              "attrs": [
                "temperature"
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
    orion.subscribe(subscription)

    orion.insert(entity)

    import time;time.sleep(3)  # Give time for notification to be processed.

    orion.unsubscribe(subscription)

    assert 0, 'TODO: Finish this test after adapting Translator'
    # crate = CrateTranslator()
    # crate.setup()
    # entities = crate.query()
    #
    # crate.dispose()
    # orion.delete(entity_id)
    #
    # assert len(entities) == 1
    # assert entities[0] == entity
