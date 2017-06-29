from client.client import HEADERS, HEADERS_PUT
from client.fixtures import entity, fresh_db, orion_client
from flask import url_for
from translators.crate import CrateTranslator
from translators.fixtures import crate_translator
from unittest.mock import patch
from utils.common import assert_ngsi_entity_equals
from utils.hosts import LOCAL
import json
import pytest
import requests


# TODO: Decide if tests will be run in a docker container or not.
QL_URL = "http://{}:8668".format(LOCAL)
notify_url = "{}/notify".format(QL_URL)
version_url = "{}/version".format(QL_URL)


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


def test_version():
    r = requests.get('{}'.format(version_url), headers=HEADERS)
    assert r.status_code == 200, r.text
    assert r.text == '0.0.1'


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


def test_invalid_no_value(notification):
    notification['data'][0]['temperature'].pop('value')
    r = requests.post('{}'.format(notify_url), data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 400
    assert r.text == 'Payload is missing value for temperature'


@patch('translators.crate.CrateTranslator')
def test_valid_notification(MockTranslator, live_server, notification):
    live_server.start()
    notify_url = url_for('notify', _external=True)

    r = requests.post('{}'.format(notify_url), data=json.dumps(notification), headers=HEADERS_PUT)

    assert r.status_code == 200
    assert r.text == 'Notification successfully processed'


def do_integration(entity, notify_url, orion_client, crate_translator):
    entity_id = entity['id']
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
    orion_client.subscribe(subscription)
    orion_client.insert(entity)

    import time;time.sleep(3)  # Give time for notification to be processed.

    entities = crate_translator.query()

    assert len(entities) > 0

    # Note: How Quantumleap will return entities is still not well defined. This will change.
    entities[0].pop(CrateTranslator.TIME_INDEX_NAME)
    entity.pop('pressure')
    entity['temperature'].pop('metadata')

    assert_ngsi_entity_equals(entities[0], entity)


def test_integration(entity, orion_client, fresh_db, crate_translator):
    """
    Test Reporter using input directly from an Orion notification and output directly to Cratedb.
    """
    not_url = notify_url.replace(LOCAL, "quantumleap")
    do_integration(entity, not_url, orion_client, crate_translator)


# def test_dev_integration(entity, orion_client, fresh_db, crate_translator):
#     """
#     Leave this for easier debugging.
#     """
#     # Remember to sudo ifconfig lo0 alias 192.0.0.1 to get notification from containerized orion!
#     # And to setup DB_HOST in reporter.py to LOCAL
#     notify_url = 'http://192.0.0.1:8668/notify'
#     do_integration(entity, notify_url, orion_client, crate_translator)
