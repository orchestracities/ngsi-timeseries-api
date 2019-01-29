from datetime import datetime
from conftest import QL_URL
from utils.common import assert_equal_time_index_arrays
import copy
import json
import pytest
import requests
import time

notify_url = "{}/notify".format(QL_URL)
HEADERS_PUT = {'Content-Type': 'application/json'}


def test_invalid_no_body(clean_mongo, clean_crate):
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(None),
                      headers=HEADERS_PUT)
    assert r.status_code == 400
    assert r.json() == {
        'detail': 'Request body is not valid JSON',
        'status': 400,
        'title': 'Bad Request',
        'type': 'about:blank'
    }


def test_invalid_empty_body(clean_mongo, clean_crate):
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps({}),
                      headers=HEADERS_PUT)
    assert r.status_code == 400
    assert r.json()['detail'] == "'data' is a required property"


def test_invalid_no_type(notification, clean_mongo, clean_crate):
    notification['data'][0].pop('type')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 400
    assert r.json() == {'detail': "'type' is a required property",
                        'status': 400,
                        'title': 'Bad Request',
                        'type': 'about:blank'}


def test_invalid_no_id(notification, clean_mongo, clean_crate):
    notification['data'][0].pop('id')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 400
    assert r.json() == {'detail': "'id' is a required property",
                        'status': 400,
                        'title': 'Bad Request',
                        'type': 'about:blank'}


def test_invalid_no_attr(notification, clean_mongo, clean_crate):
    notification['data'][0].pop('temperature')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 200


def test_invalid_no_value(notification, clean_mongo, clean_crate):
    notification['data'][0]['temperature'].pop('value')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 200


def test_valid_notification(notification, clean_mongo, clean_crate):
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=HEADERS_PUT)

    assert r.status_code == 200
    assert r.json() == 'Notification successfully processed'


def test_valid_no_modified(notification, clean_mongo, clean_crate):
    notification['data'][0]['temperature']['metadata'].pop('dateModified')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 200
    assert r.json() == 'Notification successfully processed'


def do_integration(entity, notify_url, orion_client, crate_translator):
    entity_id = entity['id']
    subscription = {
        "description": "Integration Test subscription",
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
        "throttling": 1,
    }
    orion_client.subscribe(subscription)
    time.sleep(2)

    orion_client.insert(entity)
    time.sleep(4)  # Give time for notification to be processed.
    crate_translator._refresh([entity['type']])

    entities = crate_translator.query()
    assert len(entities) == 1

    assert entities[0]['id'] == entity['id']
    assert entities[0]['type'] == entity['type']
    obtained_values = entities[0]['temperature']['values']

    # Not exactly one because first insert generates 2 notifications, see...
    # https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions
    expected_value = entity['temperature']['value']
    assert obtained_values[0] == pytest.approx(expected_value)


def test_integration(entity, orion_client, clean_mongo, crate_translator):
    """
    Test Reporter using input directly from an Orion notification and output
    directly to Cratedb.
    """
    do_integration(entity, notify_url, orion_client, crate_translator)


def test_air_quality_observed(air_quality_observed, orion_client, clean_mongo,
                              crate_translator):
    entity = air_quality_observed
    subscription = {
        "description": "Test subscription",
        "subject": {
            "entities": [
              {
                "id": entity['id'],
                "type": entity['type']
              }
            ],
            "condition": {
              "attrs": []  # all attributes
            }
          },
        "notification": {
            "http": {
              "url": notify_url
            },
            "attrs": [],  # all attributes
            "metadata": ["dateCreated", "dateModified"]
        }
    }
    orion_client.subscribe(subscription)
    orion_client.insert(entity)

    time.sleep(3)  # Give time for notification to be processed.

    entities = crate_translator.query()
    assert len(entities) == 1


@pytest.mark.skip(reason="See issue #105")
def test_geocoding(notification, clean_mongo, crate_translator):
    # Add an address attribute to the entity
    notification['data'][0]['address'] = {
        'type': 'StructuredValue',
        'value': {
            "streetAddress": "Kaivokatu",
            "postOfficeBoxNumber": "1",
            "addressLocality": "Helsinki",
            "addressCountry": "FI",
        },
        'metadata': {
            'dateModified': {
                'type': 'DateTime',
                'value': '2017-06-19T11:46:45.00Z'
            }
        }
    }
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 200
    assert r.json() == 'Notification successfully processed'

    time.sleep(3)  # Give time for notification to be processed.

    entities = crate_translator.query()
    assert len(entities) == 1

    assert 'location' in entities[0]
    assert entities[0]['location']['type'] == 'geo:point'
    lon, lat = entities[0]['location']['values'][0].split(',')
    assert float(lon) == pytest.approx(60.1707129, abs=1e-2)
    assert float(lat) == pytest.approx(24.9412167, abs=1e-2)


def test_no_multiple_data_elements(notification, clean_mongo, clean_crate):
    second_element = {
                        'id': 'Room2',
                        'type': 'Room',
                        'temperature': {
                            'type': 'Number',
                            'value': 30,
                            'metadata': {
                                'dateModified': {
                                    'type': 'DateTime',
                                    'value': '2017-06-20T11:46:45.00Z'
                                }
                            }
                        }
                    }
    notification['data'].append(second_element)
    print(json.dumps(notification))
    r = requests.post('{}'.format(notify_url), data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 400
    assert r.json() == 'Multiple data elements in notifications not ' \
                       'supported yet'


def test_time_index(notification, clean_mongo, crate_translator):
    # If present, use entity-level dateModified as time_index
    global_modified = datetime(2000, 1, 2).isoformat()
    modified = {
        'type': 'DateTime',
        'value': global_modified
    }
    notification['data'][0]['dateModified'] = modified

    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 200
    assert r.json() == 'Notification successfully processed'

    time.sleep(1)
    entity_type = notification['data'][0]['type']
    crate_translator._refresh([entity_type])

    entities = crate_translator.query()
    assert len(entities) == 1
    assert_equal_time_index_arrays(entities[0]['index'], [global_modified])

    # If not, use newest of changes
    notification['data'][0].pop('dateModified')
    temp = notification['data'][0]['temperature']
    notification['data'][0]['pressure'] = copy.deepcopy(temp)

    older = datetime(2001, 1, 2).isoformat()
    newer = datetime(2002, 1, 2).isoformat()
    e = notification['data'][0]
    e['temperature']['metadata']['dateModified']['value'] = older
    e['pressure']['metadata']['dateModified']['value'] = newer

    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 200
    assert r.json() == 'Notification successfully processed'

    time.sleep(1)
    crate_translator._refresh([entity_type])
    entities = crate_translator.query()
    assert len(entities) == 1
    obtained = entities[0]['index']
    assert_equal_time_index_arrays(obtained, [global_modified, newer])

    # Otherwise, use current time.
    current = datetime.now()
    notification['data'][0]['pressure'].pop('metadata')
    notification['data'][0]['temperature'].pop('metadata')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 200
    assert r.json() == 'Notification successfully processed'

    time.sleep(1)
    crate_translator._refresh([entity_type])
    entities = crate_translator.query()
    assert len(entities) == 1
    obtained = entities[0]['index']
    assert obtained[-1].startswith("{}".format(current.year))


def test_no_value_in_notification(notification):
    # No value
    notification['data'][0] = {
        'id': '299531',
        'type': 'AirQualityObserved',
        'p': {'type': 'string', 'value': '994', 'metadata': {}},
        'ti': {'type': 'ISO8601', 'value': ' ', 'metadata': {}},
        'pm10': {'type': 'string', 'metadata': {}},
        'pm25': {'type': 'string', 'value': '5', 'metadata': {}},
    }
    url = '{}'.format(notify_url)
    r = requests.post(url, data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 200

    # Empty value
    notification['data'][0] = {
        'id': '299531',
        'type': 'AirQualityObserved',
        'p': {'type': 'string', 'value': '994', 'metadata': {}},
        'pm10': {'type': 'string', 'value': '0', 'metadata': {}},
        'pm25': {'type': 'string', 'value': '', 'metadata': {}},
    }
    url = '{}'.format(notify_url)
    r = requests.post(url, data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 200
