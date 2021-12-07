from datetime import datetime, timezone
from conftest import QL_URL
from utils.tests.common import assert_equal_time_index_arrays
from reporter.conftest import create_notification
from reporter.tests.utils import delete_entity_type, wait_for_insert
from translators.sql_translator import entity_type as type_of
import copy
import json
import pytest
import requests
import time

notify_url = "{}/notify".format(QL_URL)

services = ['t1', 't2']

SLEEP_TIME = 1


def query_url(entity_type='Room', eid='Room1', attr_name='temperature',
              values=False, last=False):
    url = "{qlUrl}/entities/{entityId}/attrs/{attrName}"
    if values:
        url += '/value'
    if last:
        url += '?lastN=1'
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


def insert_data(notification: dict, http_headers: dict, service: str):
    etype = type_of(notification['data'][0])
    res_post = requests.post(
        '{}'.format(notify_url),
        data=json.dumps(notification),
        headers=http_headers)
    assert res_post.status_code == 200
    assert res_post.json().startswith('Notification successfully processed')

    wait_for_insert([etype], service, len(notification['data']))


def entities_with_different_attrs(etype: str) -> [dict]:
    entities = [
        {
            'id': 'Room1',
            'type': etype,
            'temperature': {
                'value': 24.2,
                'type': 'Number',
                'metadata': {
                    'dateModified': {
                        'type': 'DateTime',
                        'value': '2019-05-09T15:28:30.000Z'
                    }
                }
            },
            'pressure': {
                'value': 720,
                'type': 'Number',
                'metadata': {
                    'dateModified': {
                        'type': 'DateTime',
                        'value': '2019-05-09T15:28:30.000Z'
                    }
                }
            }
        },
        {
            'id': 'Room2',
            'type': etype,
            'temperature': {
                'value': 25.2,
                'type': 'Number',
                'metadata': {
                    'dateModified': {
                        'type': 'DateTime',
                        'value': '2019-05-09T15:28:30.000Z'
                    }
                }
            }
        },
        {
            'id': 'Room3',
            'type': etype,
            'temperature': {
                'value': 25.2,
                'type': 'Number',
                'metadata': {
                    'dateModified': {
                        'type': 'DateTime',
                        'value': '2019-05-09T15:28:30.000Z'
                    }
                }
            }
        }
    ]
    return entities


def find_by_type(etype: str, entities: [dict]) -> [dict]:
    return [e for e in entities if e['entityType'] == etype]


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
    insert_data(notification, notify_header(service), service)

    r = requests.get(query_url(), params=None, headers=query_header(service))
    assert r.status_code == 200, r.text
    delete_entity_type(service, 'Room')


@pytest.mark.parametrize("service", services)
def test_valid_no_modified(notification, service):
    notification['data'][0]['temperature']['metadata'].pop('dateModified')
    insert_data(notification, notify_header(service), service)

    r = requests.get(query_url(), params=None, headers=query_header(service))
    assert r.status_code == 200, r.text
    delete_entity_type(service, 'Room')


@pytest.mark.parametrize("e_type, e_value, exp_value", [
    ("Number", 1.0, 1.0),
    ("Number", 1, 1.0),
    ("Number", True, None),
    ("Number", "1.0", 1.0),
    ("Number", "2017-06-19T11:46:45.00Z", None),
    ("Integer", 1.0, 1),
    ("Integer", 1, 1),
    ("Integer", True, None),
    ("Integer", "1.0", 1),
    ("Integer", "2017-06-19T11:46:45.00Z", None),
    ("DateTime", 1.0, None),
    ("DateTime", 1, None),
    ("DateTime", True, None),
    ("DateTime", "error", None),
    ("DateTime", "2017-06-19T11:46:45.00Z", "2017-06-19T11:46:45.000+00:00"),
    ("Text", 1.0, "1.0"),
    ("Text", 1, "1"),
    ("Text", True, "True"),
    ("Text", "1.0", "1.0"),
    ("Text", "2017-06-19T11:46:45.00Z", "2017-06-19T11:46:45.00Z"),
    ("Text", ["a", "b"], "['a', 'b']"),
    ("Text", {"test": "test"}, "{'test': 'test'}"),
    ("StructuredValue", 1.0, None),
    ("StructuredValue", 1, None),
    ("StructuredValue", True, None),
    ("StructuredValue", "1.0", None),
    ("StructuredValue", "2017-06-19T11:46:45.00Z", None),
    ("StructuredValue", {"test": "test"}, {"test": "test"}),
    ("StructuredValue", ["a", "b"], ["a", "b"]),
    ("Property", 1.0, 1.0),
    ("Property", 1, 1),
    ("Property", True, True),
    ("Property", "1.0", "1.0"),
    ("Property", "2017-06-19T11:46:45.00Z", "2017-06-19T11:46:45.000+00:00"),
    ("Property", {"test": "test"}, {"test": "test"}),
    ("Property", ["a", "b"], ["a", "b"]),
])
@pytest.mark.parametrize("service", services)
def test_valid_data_for_type(
        notification,
        service,
        e_type,
        e_value,
        exp_value):
    del notification['data'][0]['temperature']

    notification['data'][0][e_type.lower()] = {
        'type': e_type,
        'value': e_value
    }
    insert_data(notification, notify_header(service), service)

    r = requests.get(
        query_url(
            attr_name=e_type.lower(),
            last=True),
        params=None,
        headers=query_header(service))
    assert r.status_code == 200
    assert r.json()['values'][0] == exp_value

    delete_entity_type(service, 'Room')


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
    insert_data(notification, notify_header(service), service)

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
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_multiple_data_elements(service, notification):
    """
    Test that the notify API can process notifications containing multiple elements in the data array.
    """
    etype = 'test_multiple_data_elements'  # avoid interfering w/ other tests
    notification['data'] = entities_with_different_attrs(etype)
    insert_data(notification, notify_header(service), service)

    entities_url = "{}/entities".format(QL_URL)
    r = requests.get(entities_url, params=None, headers=query_header(service))
    entities = find_by_type(etype, r.json())
    #          ^ i.e. don't assume there's no other data in the DB!
    # some tests don't delete their data to speed up the test run.
    assert len(entities) == 3

    delete_entity_type(service, etype)


@pytest.mark.parametrize("service", services)
def test_multiple_data_elements_invalid_different_servicepath(
        service, notification):
    """
    Test that the notify API can process notifications containing multiple elements in the data array
    and different fiwareServicePath.
    """

    notify_headers = notify_header(service)

    notify_headers[
        'Fiware-ServicePath'] = '/Test/Path1, /Test/Path1, /Test/Path2, /Test/Path3'

    etype = 'test_multiple_data_elements_invalid_different_servicepath'
    # ^ avoid interfering w/ other tests
    notification['data'] = entities_with_different_attrs(etype)

    r = requests.post('{}'.format(notify_url), data=json.dumps(notification),
                      headers=notify_headers)
    assert r.status_code == 400
    assert r.json().startswith('Notification not processed')


@pytest.mark.parametrize("service", services)
def test_multiple_data_elements_different_servicepath(
        service, notification):
    """
    Test that the notify API can process notifications containing multiple elements in the data array
    and different fiwareServicePath.
    """

    notify_headers = notify_header(service)

    notify_headers[
        'Fiware-ServicePath'] = '/Test/Path1, /Test/Path1, /Test/Path2'

    query_headers = query_header(service)

    query_headers['Fiware-ServicePath'] = '/Test'

    etype = 'test_multiple_data_elements_different_servicepath'
    # ^ avoid interfering w/ other tests
    notification['data'] = entities_with_different_attrs(etype)

    insert_data(notification, notify_headers, service)

    entities_url = "{}/entities".format(QL_URL)
    r = requests.get(entities_url, params=None, headers=query_headers)
    entities = find_by_type(etype, r.json())
    #          ^ i.e. don't assume there's no other data in the DB!
    # some tests don't delete their data to speed up the test run.
    assert len(entities) == 3

    delete_entity_type(service, etype)


@pytest.mark.parametrize("service", services)
def test_time_index(service):
    etype = 'test_time_index'  # avoid interfering w/ other tests
    notification = create_notification(entity_type=etype)

    # If present, use entity-level dateModified as time_index
    global_modified = datetime(2000, 1, 2, 0, 0, 0, 0,
                               timezone.utc).isoformat()
    modified = {
        'type': 'DateTime',
        'value': global_modified
    }
    notification['data'][0]['dateModified'] = modified
    insert_data(notification, notify_header(service), service)

    entities_url = "{}/entities".format(QL_URL)
    r = requests.get(entities_url, params=None, headers=query_header(service))
    entities = find_by_type(etype, r.json())
    #          ^ i.e. don't assume there's no other data in the DB!
    # some tests don't delete their data to speed up the test run.
    assert len(entities) == 1
    assert_equal_time_index_arrays([entities[0]['index']], [global_modified])

    # If not, use newest of changes
    notification['data'][0].pop('dateModified')
    temp = notification['data'][0]['temperature']
    notification['data'][0]['pressure'] = copy.deepcopy(temp)

    older = datetime(2001, 1, 2, 0, 0, 0, 0, timezone.utc).isoformat()
    newer = datetime(2002, 1, 2, 0, 0, 0, 0, timezone.utc).isoformat()
    e = notification['data'][0]
    e['temperature']['metadata']['dateModified']['value'] = older
    e['pressure']['metadata']['dateModified']['value'] = newer

    insert_data(notification, notify_header(service), service)
    time.sleep(SLEEP_TIME)  # still needed b/c of entity update w/ new attr

    r = requests.get(entities_url, params=None, headers=query_header(service))
    entities = find_by_type(etype, r.json())
    assert len(entities) == 1
    obtained = [entities[0]['index']]
    assert_equal_time_index_arrays(obtained, [global_modified, newer])

    # Otherwise, use current time.
    current = datetime.now()
    notification['data'][0]['pressure'].pop('metadata')
    notification['data'][0]['temperature'].pop('metadata')
    insert_data(notification, notify_header(service), service)
    time.sleep(SLEEP_TIME)  # still needed b/c of entity update w/ new attr

    r = requests.get(entities_url, params=None, headers=query_header(service))
    entities = find_by_type(etype, r.json())
    assert len(entities) == 1
    obtained = [entities[0]['index']]
    assert obtained[-1].startswith("{}".format(current.year))

    delete_entity_type(service, etype)


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
    r = requests.post(url, data=json.dumps(notification),
                      headers=notify_header(service))
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
    r = requests.post(url, data=json.dumps(notification),
                      headers=notify_header(service))
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
    r = requests.post(url, data=json.dumps(notification),
                      headers=notify_header(service))
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
    r = requests.post(url, data=json.dumps(notification),
                      headers=notify_header(service))
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
    r = requests.post(url, data=json.dumps(notification),
                      headers=notify_header(service))
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
        'pressure': {'type': 'Number', 'value': 26, 'metadata': {}},
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/Room1/attrs/temperature/value".format(QL_URL)
    url_new = '{}'.format(get_url)
    r = requests.post(url, data=json.dumps(notification),
                      headers=notify_header(service))
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
        'temperature': {'type': 'Number', 'value': 25, 'metadata': {}}
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/Room1/attrs/temperature/value".format(QL_URL)
    url_new = '{}'.format(get_url)
    r = requests.post(url, data=json.dumps(notification),
                      headers=notify_header(service))
    assert r.status_code == 200
    # Give time for notification to be processed
    time.sleep(SLEEP_TIME)
    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    assert res_get.json()['values'][1] == 25
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_with_value_no_type_for_attributes(service, notification):
    # entity with value and no type
    notification['data'][0] = {
        'id': 'Kitchen1',
        'type': 'Kitchen',
        'odour': {'type': 'Text', 'value': 'Good', 'metadata': {}},
        'temperature': {'value': 25, 'metadata': {}},
        'pressure': {'type': 'Number', 'value': 26, 'metadata': {}},
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/Kitchen1/attrs/temperature/value".format(QL_URL)
    url_new = '{}'.format(get_url)
    insert_data(notification, notify_header(service), service)

    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    assert res_get.json()['values'][0] == 25
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_no_value_with_type_for_attributes(service, notification):
    # entity with one Null value and no type
    notification['data'][0] = {
        'id': 'Hall1',
        'type': 'Hall',
        'odour': {'type': 'Text', 'value': 'Good', 'metadata': {}},
        'temperature': {'type': 'Number', 'metadata': {}},
        'pressure': {'type': 'Number', 'value': 26, 'metadata': {}},
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/Hall1/attrs/temperature/value".format(QL_URL)
    url_new = '{}'.format(get_url)
    insert_data(notification, notify_header(service), service)

    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    assert res_get.json()['values'][0] is None
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_issue_537(service, notification):
    # entity with one Null value and no type
    notification['data'][0] = {
        "id": "six",
        "type": "Thing",
        "serialNumber": {
            "type": "Text",
            "value": "type as Moosbllord, new value name doesthismatter2 and random values in an array",
            "metadata": {}},
        "doesthismatter2": {
            "type": "Moosbllord",
            "value": [
                "oglera8978sdfasd",
                "fdasfa6786sdf"],
            "metadata": {}}}
    url = '{}'.format(notify_url)
    get_url = "{}/entities/six/attrs/doesthismatter2/value".format(
        QL_URL)
    url_new = '{}'.format(get_url)
    insert_data(notification, notify_header(service), service)

    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    assert res_get.json()['values'][0] == [
        "oglera8978sdfasd",
        "fdasfa6786sdf"
    ]
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_issue_382(service, notification):
    # entity with one Null value and no type
    notification['data'][0] = {
        "id": "urn:ngsi-ld:Test:0002",
        "type": "Test",
        "errorNumber": {
            "type": "Integer",
            "value": 2
        },
        "refVacuumPump": {
            "type": "Relationship",
            "value": "urn:ngsi-ld:VacuumPump:FlexEdgePump"
        },
        "refOutgoingPallet": {
            "type": "Array",
            "value": [
                "urn:ngsi-ld:Pallet:0003",
                "urn:ngsi-ld:Pallet:0004"
            ]
        }
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/urn:ngsi-ld:Test:0002/attrs/errorNumber/value".format(
        QL_URL)
    url_new = '{}'.format(get_url)
    insert_data(notification, notify_header(service), service)

    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    assert res_get.json()['values'][0] == 2
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_json_ld(service, notification):
    # example json-ld entity
    notification['data'][0] = {
        "id": "urn:ngsi-ld:Streetlight:streetlight:guadalajara:4567",
        "type": "Streetlight",
        "location": {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": [-3.164485591715449, 40.62785133667262]
            }
        },
        "areaServed": {
            "type": "Property",
            "value": "Roundabouts city entrance"
        },
        "status": {
            "type": "Property",
            "value": "ok"
        },
        "refStreetlightGroup": {
            "type": "Relationship",
            "object": "urn:ngsi-ld:StreetlightGroup:streetlightgroup:G345"
        },
        "refStreetlightModel": {
            "type": "Relationship",
            "object": "urn:ngsi-ld:StreetlightModel:streetlightmodel:STEEL_Tubular_10m"
        },
        "circuit": {
            "type": "Property",
            "value": "C-456-A467"
        },
        "lanternHeight": {
            "type": "Property",
            "value": 10
        },
        "locationCategory": {
            "type": "Property",
            "value": "centralIsland"
        },
        "powerState": {
            "type": "Property",
            "value": "off"
        },
        "controllingMethod": {
            "type": "Property",
            "value": "individual"
        },
        "dateLastLampChange": {
            "type": "Property",
            "value": {
                "@type": "DateTime",
                "@value": "2016-07-08T08:02:21.753Z"
            }
        },
        "@context": [
            "https://schema.lab.fiware.org/ld/context",
            "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
        ]
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/urn:ngsi-ld:Streetlight:streetlight:guadalajara:4567/attrs/lanternHeight/value".format(
        QL_URL)
    url_new = '{}'.format(get_url)
    insert_data(notification, notify_header(service), service)

    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    assert res_get.json()['values'][0] == 10
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_json_ld_observed_at_meta(service, notification):
    # example json-ld entity with observedAt as metadata
    notification['data'][0] = {
        "id": "urn:ngsi-ld:Device:filling001",
        "type": "FillingSensor",
        "filling": {
            "type": "Property",
            "value": 0.94,
            "unitCode": "C62",
            "observedAt": "2021-01-28T12:33:20.000Z"
        }
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/urn:ngsi-ld:Device:filling001".format(
        QL_URL)
    url_new = '{}'.format(get_url)
    insert_data(notification, notify_header(service), service)

    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    expected_value = [notification['data'][0]['filling']['observedAt']]
    assert_equal_time_index_arrays(
        [res_get.json()['index'][0]], expected_value)
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_json_ld_modified_at_meta(service, notification):
    # example json-ld entity with modifiedAt as metadata
    notification['data'][0] = {
        "id": "urn:ngsi-ld:Device:filling001",
        "type": "FillingSensor",
        "filling": {
            "type": "Property",
            "value": 0.94,
            "unitCode": "C62",
            "modifiedAt": "2021-01-28T12:33:10.000Z"
        }
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/urn:ngsi-ld:Device:filling001".format(
        QL_URL)
    url_new = '{}'.format(get_url)
    insert_data(notification, notify_header(service), service)

    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    expected_value = [notification['data'][0]['filling']['modifiedAt']]
    assert_equal_time_index_arrays(
        [res_get.json()['index'][0]], expected_value)
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_json_ld_both_at_meta(service, notification):
    # example json-ld entity with modifiedAt and observedAt as metadata
    notification['data'][0] = {
        "id": "urn:ngsi-ld:Device:filling001",
        "type": "FillingSensor",
        "modifiedAt": "2021-01-28T12:33:22.000Z",
        "filling": {
            "type": "Property",
            "value": 0.94,
            "unitCode": "C62",
            "observedAt": "2021-01-28T12:33:20.000Z",
            "modifiedAt": "2021-01-28T12:33:22.000Z"
        }
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/urn:ngsi-ld:Device:filling001".format(
        QL_URL)
    url_new = '{}'.format(get_url)
    insert_data(notification, notify_header(service), service)

    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    expected_value = [notification['data'][0]['filling']['observedAt']]
    assert_equal_time_index_arrays(
        [res_get.json()['index'][0]], expected_value)
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_json_ld_date_modified_at_attribute(service, notification):
    # example json-ld entity with modifiedAt as attribute
    notification['data'][0] = {
        "id": "urn:ngsi-ld:Device:filling001",
        "type": "FillingSensor",
        "modifiedAt": "2021-01-28T12:33:22.000Z",
        "filling": {
            "type": "Property",
            "value": 0.94,
            "unitCode": "C62"
        }
    }
    url = '{}'.format(notify_url)
    get_url = "{}/entities/urn:ngsi-ld:Device:filling001".format(
        QL_URL)
    url_new = '{}'.format(get_url)
    insert_data(notification, notify_header(service), service)

    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    expected_value = [notification['data'][0]['modifiedAt']]
    assert_equal_time_index_arrays(
        [res_get.json()['index'][0]], expected_value)
    delete_entity_type(service, notification['data'][0]['type'])


@pytest.mark.parametrize("service", services)
def test_json_ld_date_observed(service, notification):
    # example json-ld entity with custom index property
    notification['data'][0] = {
        "id": "urn:ngsi-ld:Device:filling001",
        "type": "FillingSensor",
        "dateObserved": {
            "type": "Property",
            "value": {
                "@type": "DateTime",
                "@value": "2018-08-07T12:00:00Z"
            }
        },
        "filling": {
            "type": "Property",
            "value": 0.94,
            "unitCode": "C62",
            "observedAt": "2021-01-28T12:33:20.000Z",
            "modifiedAt": "2021-01-28T12:33:22.000Z"
        }
    }
    get_url = "{}/entities/urn:ngsi-ld:Device:filling001".format(
        QL_URL)
    url_new = '{}'.format(get_url)
    h = notify_header(service)
    h['Fiware-TimeIndex-Attribute'] = 'dateObserved'

    insert_data(notification, h, service)

    res_get = requests.get(url_new, headers=query_header(service))
    assert res_get.status_code == 200
    expected_value = [notification['data'][0]
                      ['dateObserved']['value']['@value']]
    assert_equal_time_index_arrays(
        [res_get.json()['index'][0]], expected_value)
    delete_entity_type(service, notification['data'][0]['type'])
