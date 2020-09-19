from datetime import datetime, timezone
from conftest import QL_URL
from utils.common import assert_equal_time_index_arrays
from reporter.tests.utils import delete_entity_type
import copy
import json
import pytest
import requests
import time

notify_url = "{}/notify".format(QL_URL)

services = ['t1', 't2']

SLEEP_TIME = 1


def query_url(entity_type='Room', eid='Room1', attr_name='temperature', values=False):
    url = "{qlUrl}/entities/{entityId}/attrs/{attrName}"
    if values:
        url += '/value'
    return url.format(
        qlUrl=QL_URL,
        entityId=eid,
        attrName=attr_name,
    )


def notify_header(service=None, service_path=None):
    return headers(service, service_path, True)


def query_header(service=None, service_path=None):
    return headers(service, service_path, False)


def headers(service=None, service_path=None, content_type=True):
    h = {}
    if content_type:
        h['Content-Type'] = 'application/json'
    if service:
        h['Fiware-Service'] = service
    if service_path:
        h['Fiware-ServicePath'] = service_path

    return h

@pytest.mark.parametrize("service", services)
def test_invalid_no_body(service):
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(None),
                      headers=notify_header(service))
    assert r.status_code == 400
    assert r.json() == {
        'detail': 'Request body is not valid JSON',
        'status': 400,
        'title': 'Bad Request',
        'type': 'about:blank'
    }


@pytest.mark.parametrize("service", services)
def test_invalid_empty_body(service):
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps({}),
                      headers=notify_header(service))
    assert r.status_code == 400
    assert r.json()['detail'] == "'data' is a required property"


@pytest.mark.parametrize("service", services)
def test_invalid_no_type(notification, service):
    notification['data'][0].pop('type')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=notify_header(service))
    assert r.status_code == 400
    assert r.json() == {'detail': "'type' is a required property - 'data.0'",
                        'status': 400,
                        'title': 'Bad Request',
                        'type': 'about:blank'}


@pytest.mark.parametrize("service", services)
def test_invalid_no_id(notification, service):
    notification['data'][0].pop('id')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=notify_header(service))
    assert r.status_code == 400
    assert r.json() == {'detail': "'id' is a required property - 'data.0'",
                        'status': 400,
                        'title': 'Bad Request',
                        'type': 'about:blank'}


@pytest.mark.parametrize("service", services)
def test_invalid_no_attr(notification, service):
    notification['data'][0].pop('temperature')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=notify_header(service))
    assert r.status_code == 200
    delete_entity_type(service, 'Room')


@pytest.mark.parametrize("service", services)
def test_invalid_no_value(notification, service):
    notification['data'][0]['temperature'].pop('value')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=notify_header(service))
    assert r.status_code == 200
    delete_entity_type(service, 'Room')


@pytest.mark.parametrize("service", services)
def test_valid_notification(notification, service):
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=notify_header(service))
    assert r.status_code == 200
    assert r.json().startswith('Notification successfully processed')
    time.sleep(SLEEP_TIME)
    r = requests.get(query_url(), params=None, headers=query_header(service))
    assert r.status_code == 200, r.text
    delete_entity_type(service, 'Room')


@pytest.mark.parametrize("service", services)
def test_valid_no_modified(notification, service):
    notification['data'][0]['temperature']['metadata'].pop('dateModified')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=notify_header(service))
    assert r.status_code == 200
    assert r.json().startswith('Notification successfully processed')
    time.sleep(SLEEP_TIME)
    r = requests.get(query_url(), params=None, headers=query_header(service))
    assert r.status_code == 200, r.text
    delete_entity_type(service, 'Room')


def do_integration(entity, subscription, orion_client, service=None, service_path=None):
    orion_client.subscribe(subscription, service, service_path)
    time.sleep(SLEEP_TIME)

    orion_client.insert(entity, service, service_path)
    time.sleep(2 * SLEEP_TIME)  # Give time for notification to be processed.

    entities_url = "{}/entities".format(QL_URL)

    r = requests.get(entities_url, params=None, headers=None)
    assert r.status_code == 200
    entities = r.json()
    assert len(entities) == 1

    assert entities[0]['id'] == entity['id']
    assert entities[0]['type'] == entity['type']

    delete_entity_type(None, entity['type'])


def test_integration(entity, orion_client):
    """
    Test Reporter using input directly from an Orion notification and output
    directly to Cratedb.
    """
    subscription = {
        "description": "Integration Test subscription",
        "subject": {
            "entities": [
                {
                    "id": entity['id'],
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
    do_integration(entity, subscription, orion_client)


def test_air_quality_observed(air_quality_observed, orion_client):
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
    do_integration(entity, subscription, orion_client)



def test_integration_multiple_entities(diffEntityWithDifferentAttrs, orion_client):
    """
    Test Reporter using input directly from an Orion notification and output
    directly to Cratedb.
    """


    subscription = {
        "description": "Integration Test subscription",
        "subject": {
            "entities": [
                {
                    "idPattern": ".*",
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
        "throttling": 5,
    }
    orion_client.subscribe(subscription, "service", "/Root/#")

    for idx, e in enumerate(diffEntityWithDifferentAttrs):
        orion_client.insert(e, "service", "/Root/{}".format(idx))
    time.sleep(4 * SLEEP_TIME)  # Give time for notification to be processed.

    entities_url = "{}/entities".format(QL_URL)

    r = requests.get(entities_url, params=None, headers=query_header("service", "/Root"))
    assert r.status_code == 200
    entities = r.json()
    assert len(entities) == 3
    delete_entity_type("service", diffEntityWithDifferentAttrs[0]['type'])

@pytest.mark.skip(reason="See issue #105")
@pytest.mark.parametrize("service", services)
def test_geocoding(service, notification):
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
                      headers=notify_header(service))
    assert r.status_code == 200
    assert r.json() == 'Notification successfully processed'

    time.sleep(2 * SLEEP_TIME)  # Give time for notification to be processed.

    entities_url = "{}/entities".format(QL_URL)

    r = requests.get(entities_url, params=None, headers=query_header(service))
    assert r.status_code == 200
    entities = r.json()
    assert len(entities) == 1

    assert 'location' in entities[0]
    assert entities[0]['location']['type'] == 'geo:point'
    lon, lat = entities[0]['location']['values'][0].split(',')
    assert float(lon) == pytest.approx(60.1707129, abs=1e-2)
    assert float(lat) == pytest.approx(24.9412167, abs=1e-2)
    delete_entity_type(service,  notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_multiple_data_elements(service, notification, diffEntityWithDifferentAttrs):
    """
    Test that the notify API can process notifications containing multiple elements in the data array.
    """
    notification['data'] = diffEntityWithDifferentAttrs
    r = requests.post('{}'.format(notify_url), data=json.dumps(notification),
                      headers=notify_header(service))
    assert r.status_code == 200
    assert r.json().startswith('Notification successfully processed')

    entities_url = "{}/entities".format(QL_URL)
    time.sleep(SLEEP_TIME)
    r = requests.get(entities_url, params=None, headers=query_header(service))
    entities = r.json()
    assert len(entities) == 3
    delete_entity_type(None, diffEntityWithDifferentAttrs[0]['type'])


@pytest.mark.parametrize("service", services)
def test_multiple_data_elements_invalid_different_servicepath(service, notification, diffEntityWithDifferentAttrs):
    """
    Test that the notify API can process notifications containing multiple elements in the data array
    and different fiwareServicePath.
    """

    notify_headers = notify_header(service)

    notify_headers['Fiware-ServicePath'] = '/Test/Path1, /Test/Path1, /Test/Path2, /Test/Path3'

    notification['data'] = diffEntityWithDifferentAttrs

    r = requests.post('{}'.format(notify_url), data=json.dumps(notification),
                      headers=notify_headers)
    assert r.status_code == 400
    assert r.json().startswith('Notification not processed')


@pytest.mark.parametrize("service", services)
def test_multiple_data_elements_different_servicepath(service, notification, diffEntityWithDifferentAttrs):
    """
    Test that the notify API can process notifications containing multiple elements in the data array
    and different fiwareServicePath.
    """

    notify_headers = notify_header(service)

    notify_headers['Fiware-ServicePath'] = '/Test/Path1, /Test/Path1, /Test/Path2'

    query_headers = query_header(service)

    query_headers['Fiware-ServicePath'] = '/Test'

    notification['data'] = diffEntityWithDifferentAttrs

    r = requests.post('{}'.format(notify_url), data=json.dumps(notification),
                      headers=notify_headers)
    assert r.status_code == 200
    assert r.json().startswith('Notification successfully processed')

    entities_url = "{}/entities".format(QL_URL)
    time.sleep(SLEEP_TIME)
    r = requests.get(entities_url, params=None, headers=query_headers)
    entities = r.json()
    assert len(entities) == 3
    delete_entity_type(service, diffEntityWithDifferentAttrs[0]['type'])


@pytest.mark.parametrize("service", services)
def test_time_index(service, notification):
    # If present, use entity-level dateModified as time_index
    global_modified = datetime(2000, 1, 2, 0, 0, 0, 0, timezone.utc).isoformat()
    modified = {
        'type': 'DateTime',
        'value': global_modified
    }
    notification['data'][0]['dateModified'] = modified

    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=notify_header(service))
    assert r.status_code == 200
    assert r.json().startswith('Notification successfully processed')

    time.sleep(SLEEP_TIME)
    entity_type = notification['data'][0]['type']

    entities_url = "{}/entities".format(QL_URL)
    time.sleep(SLEEP_TIME)
    r = requests.get(entities_url, params=None, headers=query_header(service))
    entities = r.json()
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
                      headers=notify_header(service))
    assert r.status_code == 200
    assert r.json().startswith('Notification successfully processed')

    time.sleep(SLEEP_TIME)
    r = requests.get(entities_url, params=None, headers=query_header(service))
    entities = r.json()
    assert len(entities) == 1
    obtained = entities[0]['index']
    assert_equal_time_index_arrays(obtained, [global_modified, newer])

    # Otherwise, use current time.
    current = datetime.now()
    notification['data'][0]['pressure'].pop('metadata')
    notification['data'][0]['temperature'].pop('metadata')
    r = requests.post('{}'.format(notify_url),
                      data=json.dumps(notification),
                      headers=notify_header(service))
    assert r.status_code == 200
    assert r.json().startswith('Notification successfully processed')

    time.sleep(SLEEP_TIME)
    r = requests.get(entities_url, params=None, headers=query_header(service))
    entities = r.json()
    assert len(entities) == 1
    obtained = entities[0]['index']
    assert obtained[-1].startswith("{}".format(current.year))
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_no_value_in_notification(service, notification):
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
    r = requests.post(url, data=json.dumps(notification), headers=notify_header(service))
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
    r = requests.post(url, data=json.dumps(notification), headers=notify_header(service))
    assert r.status_code == 200
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_no_value_for_attributes(service, notification):
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
    r = requests.post(url, data=json.dumps(notification), headers=notify_header(service))
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(SLEEP_TIME)
    res_get = requests.get(url_new, headers=notify_header(service))
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
    r = requests.post(url, data=json.dumps(notification), headers=notify_header(service))
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(SLEEP_TIME)
    res_get = requests.get(url_new, headers=query_header(service))
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
    r = requests.post(url, data=json.dumps(notification), headers=notify_header(service))
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(SLEEP_TIME)
    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    assert res_get.json()['values'][0] == '10'
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_no_value_no_type_for_attributes(service, notification):
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
    r = requests.post(url, data=json.dumps(notification), headers=notify_header(service))
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(SLEEP_TIME)
    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 404
    # Get value of attribute having value
    get_url_new = "{}/entities/Room1/attrs/pressure/value".format(QL_URL)
    url_new = '{}'.format(get_url_new)
    res_get = requests.get(url_new, headers=query_header(service))
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
    r = requests.post(url, data=json.dumps(notification), headers=notify_header(service))
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(SLEEP_TIME)
    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    assert res_get.json()['values'][1] == '25'
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_with_value_no_type_for_attributes(service, notification):
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
    r = requests.post(url, data=json.dumps(notification), headers=notify_header(service))
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(SLEEP_TIME)
    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    assert res_get.json()['values'][0] == '25'
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_no_value_with_type_for_attributes(service, notification):
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
    r = requests.post(url, data=json.dumps(notification), headers=notify_header(service))
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(SLEEP_TIME)
    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    assert res_get.json()['values'][0] == None
    delete_entity_type(service, notification['data'][0]['type'])