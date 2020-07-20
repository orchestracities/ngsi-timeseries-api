from datetime import datetime, timezone
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
    assert r.json() == {'detail': "'type' is a required property - 'data.0'",
                        'status': 400,
                        'title': 'Bad Request',
                        'type': 'about:blank'}


def test_invalid_no_id(notification, clean_mongo, clean_crate):
    notification['data'][0].pop('id')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 400
    assert r.json() == {'detail': "'id' is a required property - 'data.0'",
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


def test_multiple_data_elements(notification, sameEntityWithDifferentAttrs, clean_mongo, clean_crate):
    """
    Test that the notify API can process notifications containing multiple elements in the data array.
    """
    notification['data'] = sameEntityWithDifferentAttrs
    r = requests.post('{}'.format(notify_url), data=json.dumps(notification),
                      headers=HEADERS_PUT)
    assert r.status_code == 200
    assert r.json() == 'Notification successfully processed'


def test_time_index(notification, clean_mongo, crate_translator):
    # If present, use entity-level dateModified as time_index
    global_modified = datetime(2000, 1, 2, 0, 0, 0, 0, timezone.utc).isoformat()
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

    older = datetime(2001, 1, 2, 0, 0, 0, 0, timezone.utc).isoformat()
    newer = datetime(2002, 1, 2, 0, 0, 0, 0, timezone.utc).isoformat()
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

    
def test_no_value_for_attributes(notification):
    # with empty value
    notification['data'][0] = {
        'id': '299531',
        'type': 'AirQualityObserved',
        'p': {'type': 'string', 'value': '', 'metadata': {}},
        'pm10': {'type': 'string', 'value': '', 'metadata': {}},
        'pm25': {'type': 'string', 'value': '', 'metadata': {}},
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/299531".format(QL_URL)
    url_new = '{}'.format(get_url)
    r = requests.post(url, data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 200
    res_get = requests.get(url_new, headers=HEADERS_PUT)
    assert res_get.status_code == 404
    # entity with missing value string
    notification['data'][0] = {
        'id': '299531',
        'type': 'AirQualityObserved',
        'p': {'type': 'string'},
        'pm10': {'type': 'string', 'value': '', 'metadata': {}},
        'pm25': {'type': 'string', 'value': '', 'metadata': {}},
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/299531/attrs/p/value".format(QL_URL)
    url_new = '{}'.format(get_url)
    r = requests.post(url, data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 200
    res_get = requests.get(url_new, headers=HEADERS_PUT)
    assert res_get.status_code == 404
    # entity has both valid and empty attributes
    notification['data'][0] = {
        'id': '299531',
        'type': 'AirQualityObserved',
        'p': {'type': 'string'},
        'pm10': {'type': 'string', 'value': '10', 'metadata': {}},
    }
    url = '{}'.format(notify_url)
    get_url_new = "{}/entities/299531/attrs/pm10/value".format(QL_URL)
    url_new = '{}'.format(get_url_new)
    r = requests.post(url, data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(3)
    res_get = requests.get(url_new, headers=HEADERS_PUT)
    assert res_get.status_code == 200
    assert res_get.json()['values'][2] == '10'

def test_no_value_no_type_for_attributes(notification):
    # entity with no value and no type
    notification['data'][0] = {
        'id': 'Room1',
        'type': 'Room',
        'odour': {'type': 'Text', 'value': 'Good', 'metadata': {}},
        'temperature': {'metadata': {}},
        'pressure': {'type': 'Number', 'value': '26', 'metadata': {}},
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/Room1/attrs/temperature/value".format(QL_URL)
    url_new = '{}'.format(get_url)
    r = requests.post(url, data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(3)
    res_get = requests.get(url_new, headers=HEADERS_PUT)
    assert res_get.status_code == 404
    # Get value of attribute having value
    get_url_new = "{}/entities/Room1/attrs/pressure/value".format(QL_URL)
    url_new = '{}'.format(get_url_new)
    res_get = requests.get(url_new, headers=HEADERS_PUT)
    assert res_get.status_code == 200
    assert res_get.json()['values'][0] == 26

    # entity with value other than Null
    notification['data'][0] = {
        'id': 'Room1',
        'type': 'Room',
        'temperature': {'type': 'Number', 'value': '25', 'metadata': {}}
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/Room1/attrs/temperature/value".format(QL_URL)
    url_new = '{}'.format(get_url)
    r = requests.post(url, data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(3)
    res_get = requests.get(url_new, headers=HEADERS_PUT)
    assert res_get.status_code == 200
    assert res_get.json()['values'][1] == '25'


def test_with_value_no_type_for_attributes(notification):
    # entity with value and no type
    notification['data'][0] = {
        'id': 'Kitchen1',
        'type': 'Kitchen',
        'odour': {'type': 'Text', 'value': 'Good', 'metadata': {}},
        'temperature': {'value': '25', 'metadata': {}},
        'pressure': {'type': 'Number', 'value': '26', 'metadata': {}},
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/Kitchen1/attrs/temperature/value".format(QL_URL)
    url_new = '{}'.format(get_url)
    r = requests.post(url, data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(3)
    res_get = requests.get(url_new, headers=HEADERS_PUT)
    assert res_get.status_code == 200
    assert res_get.json()['values'][0] == '25'

def test_no_value_with_type_for_attributes(notification):
    # entity with one Null value and no type
    notification['data'][0] = {
        'id': 'Hall1',
        'type': 'Hall',
        'odour': {'type': 'Text', 'value': 'Good', 'metadata': {}},
        'temperature': {'type': 'Number', 'metadata': {}},
        'pressure': {'type': 'Number', 'value': '26', 'metadata': {}},
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/Hall1/attrs/temperature/value".format(QL_URL)
    url_new = '{}'.format(get_url)
    r = requests.post(url, data=json.dumps(notification), headers=HEADERS_PUT)
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(3)
    res_get = requests.get(url_new, headers=HEADERS_PUT)
    assert res_get.status_code == 200
    assert res_get.json()['values'][0] == None


