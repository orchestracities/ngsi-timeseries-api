import pytest
import requests
import time
import json

from tests.common import load_data, check_data, unload_data, \
    check_deleted_data, QL_URL_4ORION, ORION_URL_4QL
from reporter.tests.utils import delete_entity_type
from reporter.tests.utils import delete_test_data
from conftest import *
from reporter.timex import TIME_INDEX_HEADER_NAME
from reporter.subscription_builder import build_subscription


def notify_header(service=None, service_path=None):
    return headers(service, service_path, True)


def query_header(service=None, service_path=None):
    return headers(service, service_path, False)


notify_url = "{}/v2/notify".format(QL_URL_4ORION)

subscribe_url = "{}/subscribe".format(QL_URL)

services = ['t1', 't2']

SLEEP_TIME = 1


def headers(service=None, service_path=None, content_type=True):
    h = {}
    if content_type:
        h['Content-Type'] = 'application/json'
    if service:
        h['Fiware-Service'] = service
    if service_path:
        h['Fiware-ServicePath'] = service_path

    return h


def test_integration_basic():
    entities = []
    try:
        entities = load_data()
        assert len(entities) > 1
        check_data(entities)
    finally:
        unload_data(entities)
        check_deleted_data(entities)


def do_integration(entity, subscription, orion_client, service=None,
                   service_path=None):
    subscription_id = orion_client.subscribe(subscription, service,
                                             service_path). \
        headers['Location'][18:]
    time.sleep(SLEEP_TIME)

    orion_client.insert(entity, service, service_path)
    time.sleep(4 * SLEEP_TIME)  # Give time for notification to be processed.

    entities_url = "{}/entities".format(QL_URL)

    h = headers(service=service, service_path=service_path, content_type=False)

    r = requests.get(entities_url, params=None, headers=h)
    assert r.status_code == 200
    entities = r.json()
    assert len(entities) == 1

    assert entities[0]['id'] == entity['id']
    assert entities[0]['type'] == entity['type']

    delete_entity_type(service, entity['type'], service_path)
    orion_client.delete(entity['id'], service, service_path)
    orion_client.delete_subscription(subscription_id, service,
                                     service_path)


@pytest.mark.parametrize("service", services)
def test_integration(service, entity, orion_client):
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
    do_integration(entity, subscription, orion_client, service, "/")


@pytest.mark.parametrize("service", services)
def test_air_quality_observed(service, air_quality_observed, orion_client):
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
    do_integration(entity, subscription, orion_client, service, "/")


@pytest.mark.skip("weird")
@pytest.mark.parametrize("service", services)
def test_integration_multiple_entities(service, diffEntityWithDifferentAttrs,
                                       orion_client):
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
        "throttling": 1,
    }
    subscription_id = orion_client.subscribe(subscription, service,
                                             "/Root/#"). \
        headers['Location'][18:]

    for idx, e in enumerate(diffEntityWithDifferentAttrs):
        orion_client.insert(e, service, "/Root/{}".format(idx))
    time.sleep(10 * SLEEP_TIME)  # Give time for notification to be processed.

    entities_url = "{}/entities".format(QL_URL)

    r = requests.get(entities_url, params=None,
                     headers=query_header(service, "/Root"))
    assert r.status_code == 200
    entities = r.json()
    assert len(entities) == 3
    delete_entity_type(service, diffEntityWithDifferentAttrs[0]['type'],
                       "/Root")

    for idx, e in enumerate(diffEntityWithDifferentAttrs):
        orion_client.insert(e, service, "/Root/{}".format(idx))
        orion_client.delete(e['id'], service, "/Root/{}".format(idx))
    orion_client.delete_subscription(subscription_id, service,
                                     "/Root/#")


@pytest.mark.skip("weird")
@pytest.mark.parametrize("service", services)
def test_integration_multiple_values(service, entity, orion_client,
                                     clean_mongo):
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
                "attrs": []  # all attributes
            }
        },
        "notification": {
            "http": {
                "url": notify_url
            },
            "attrs": [],  # all attributes
            "metadata": ["dateCreated", "dateModified"]
        },
        "throttling": 1,
    }
    subscription_id = orion_client.subscribe(subscription, service, '/'). \
        headers['Location'][18:]
    time.sleep(SLEEP_TIME)

    orion_client.insert(entity, service, '/')
    time.sleep(4 * SLEEP_TIME)  # Give time for notification to be processed.

    # Update values in Orion
    for i in range(1, 4):
        attrs = {
            'temperature': {
                'value': entity['temperature']['value'] + i,
                'type': 'Number',
            },
            'pressure': {
                'value': entity['pressure']['value'] + i,
                'type': 'Number',
            },
        }
        orion_client.update_attr(entity['id'], attrs, service, '/')
        time.sleep(1)

    # Query in Quantumleap
    query_params = {
        'type': entity['type'],
    }
    query_url = "{qlUrl}/entities/{entityId}".format(
        qlUrl=QL_URL,
        entityId=entity['id'],
    )
    r = requests.get(query_url, params=query_params,
                     headers=query_header(service, "/"))
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data['index']) > 1
    assert len(data['attributes']) == 2

    # Note some notifications may have been lost
    pressures = data['attributes'][0]['values']
    assert set(pressures).issubset(set([720.0, 721.0, 722.0, 723.0]))
    temperatures = data['attributes'][1]['values']
    assert set(temperatures).issubset(set([24.2, 25.2, 26.2, 27.2]))
    delete_entity_type(service, entity['type'], "/")
    orion_client.delete(entity['id'], service, '/')
    orion_client.delete_subscription(subscription_id, service, '/')


@pytest.mark.skip("weird")
@pytest.mark.parametrize("service", services)
def test_integration_custom_index(service, entity, orion_client, clean_mongo):
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
                "attrs": []  # all attributes
            }
        },
        "notification": {
            "httpCustom": {
                "url": notify_url,
                "headers": {
                    "Fiware-TimeIndex-Attribute": "myCustomIndex"
                },
            },
            "attrs": [],  # all attributes
            "metadata": ["dateCreated", "dateModified"]
        },
        "throttling": 1,
    }

    orion_client.subscribe(subscription, service, '/')
    time.sleep(SLEEP_TIME)

    # Insert values in Orion
    entity['myCustomIndex'] = {
        'value': '2019-08-22T18:22:00',
        'type': 'DateTime',
        'metadata': {}
    }
    entity.pop('temperature')
    entity.pop('pressure')

    orion_client.insert(entity, service, '/')
    time.sleep(4 * SLEEP_TIME)  # Give time for notification to be processed.

    # Update values in Orion
    for i in range(1, 4):
        attrs = {
            'myCustomIndex': {
                'value': '2019-08-22T18:22:0{}'.format(i),
                'type': 'DateTime',
            },
        }
        orion_client.update_attr(entity['id'], attrs, service, '/')
        time.sleep(1)

    # Query in Quantumleap
    query_params = {
        'type': entity['type'],
    }
    query_url = "{qlUrl}/entities/{entityId}".format(
        qlUrl=QL_URL,
        entityId=entity['id'],
    )
    r = requests.get(query_url, params=query_params,
                     headers=query_header(service, "/"))
    assert r.status_code == 200, r.text

    data = r.json()
    # Note some notifications may have been lost
    assert data['attributes'][0]['values'] == data['index']
    assert len(data['index']) > 1
    delete_entity_type(service, entity['type'], '/')


"""
Multitenancy is implemented very similarly as in Orion.

The tenants will be specified with the use of the Fiware-Service HTTP header.
Database Tables of different tenants will be isolated with the use of schemas.
This means, one schema per tenant (i.e, per Fiware-Service).

Entities will be associated to a Fiware-ServicePath also, just like in Orion.
The service path is a hierarchical path such as "/eu/greece" or "/eu/italy".
You can insert entities using "/eu/italy" service path, and retrieve them with
a query using either the same or just "/eu/" service path. It will not return
results if used with "/eu/greece" or any other deviation from the path used at
insertion.
"""


@pytest.mark.skip("deprecated")
@pytest.mark.parametrize("service", services)
def test_integration_with_orion(clean_mongo, service, entity):
    """
    Make sure QL correctly handles headers in Orion's notification
    """
    h = {
        'Content-Type': 'application/json',
        'Fiware-Service': service,
        'Fiware-ServicePath': '/',
    }

    # Subscribe QL to Orion
    params = {
        'orionUrl': ORION_URL_4QL,
        'quantumleapUrl': QL_URL_4ORION,
    }
    r = requests.post(subscribe_url, params=params, headers=h)
    assert r.status_code == 201

    # Insert values in Orion with Service and ServicePath
    data = json.dumps(entity)
    r = requests.post('{}/entities'.format(ORION_URL), data=data, headers=h)
    assert r.ok

    # Wait notification to be processed
    time.sleep(2)

    # Query WITH headers
    url = "{qlUrl}/entities/{entityId}".format(
        qlUrl=QL_URL,
        entityId=entity['id'],
    )
    query_params = {
        'type': entity['type'],
    }
    r = requests.get('{}'.format(url), params=query_params, headers=h)
    assert r.status_code == 200, r.text
    obtained = r.json()
    assert obtained['entityId'] == entity['id']

    # Query WITHOUT headers
    r = requests.get(url, params=query_params)
    assert r.status_code == 404, r.text
    delete_test_data(service, ["Room"])


'''
build subscription tests
'''


@pytest.mark.skip("deprecated")
def test_bare_subscription():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        attributes=None, observed_attributes=None, notified_attributes=None,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified', 'TimeInstant',
                         'timestamp']
        },
        'throttling': 1
    }

    assert actual == expected


@pytest.mark.skip("deprecated")
def test_entity_type():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype='gauge', eid=None, eid_pattern=None,
        attributes=None, observed_attributes=None, notified_attributes=None,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'type': 'gauge',
                'idPattern': '.*'
            }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified', 'TimeInstant',
                         'timestamp']
        },
        'throttling': 1
    }

    assert actual == expected


@pytest.mark.skip("deprecated")
def test_entity_id():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=123, eid_pattern=None,
        attributes=None, observed_attributes=None, notified_attributes=None,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'id': '123'
            }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified', 'TimeInstant',
                         'timestamp']
        },
        'throttling': 1
    }

    assert actual == expected


@pytest.mark.skip("deprecated")
@pytest.mark.parametrize('attrs', ['a1', 'a1,a2', 'a1,a2,a3'])
def test_attributes(attrs):
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        attributes=attrs, observed_attributes=None, notified_attributes=None,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }],
            'condition': {
                'attrs': attrs.split(',')
            }
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'attrs': attrs.split(','),
            'metadata': ['dateCreated', 'dateModified', 'TimeInstant',
                         'timestamp']
        },
        'throttling': 1
    }

    assert actual == expected


@pytest.mark.parametrize('attrs', ['a1', 'a1,a2', 'a1,a2,a3'])
def test_observed_attributes(attrs):
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        attributes=None, observed_attributes=attrs, notified_attributes=None,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }],
            'condition': {
                'attrs': attrs.split(',')
            }
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified', 'TimeInstant',
                         'timestamp']
        },
        'throttling': 1
    }

    assert actual == expected


@pytest.mark.skip("deprecated")
@pytest.mark.parametrize('attrs', ['a1', 'a1,a2', 'a1,a2,a3'])
def test_notified_attributes(attrs):
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        attributes=None, observed_attributes=None, notified_attributes=attrs,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'attrs': attrs.split(','),
            'metadata': ['dateCreated', 'dateModified', 'TimeInstant',
                         'timestamp']
        },
        'throttling': 1
    }

    assert actual == expected


@pytest.mark.skip("deprecated")
def test_throttling():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        attributes=None, observed_attributes=None, notified_attributes=None,
        throttling_secs=123)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified', 'TimeInstant',
                         'timestamp']
        },
        'throttling': 123
    }

    assert actual == expected


@pytest.mark.skip("deprecated")
def test_entity_id_overrides_pattern():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid='e123', eid_pattern='e1.*',
        attributes=None, observed_attributes=None, notified_attributes=None,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'id': 'e123'
            }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified', 'TimeInstant',
                         'timestamp']
        },
        'throttling': 1
    }

    assert actual == expected


@pytest.mark.skip("deprecated")
def test_all_attributes():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        attributes=None, observed_attributes='a,b', notified_attributes='b,c',
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }],
            'condition': {
                'attrs': ['a', 'b']
            }
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'attrs': ['b', 'c'],
            'metadata': ['dateCreated', 'dateModified', 'TimeInstant',
                         'timestamp']
        },
        'throttling': 1
    }

    assert actual == expected


@pytest.mark.skip("deprecated")
@pytest.mark.parametrize("observed,notified", [
    (None, 'b'),
    ('a', None),
    ('a', 'b')])
def test_attributes_overrides_other_attributes(observed, notified):
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        attributes='x',
        observed_attributes=observed, notified_attributes=notified,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }],
            'condition': {
                'attrs': ['x']
            }
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'attrs': ['x'],
            'metadata': ['dateCreated', 'dateModified', 'TimeInstant',
                         'timestamp']
        },
        'throttling': 1
    }

    assert actual == expected


@pytest.mark.skip("deprecated")
def test_subscription_with_time_index():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        attributes=None, observed_attributes=None, notified_attributes=None,
        throttling_secs=None,
        time_index_attribute='my-time-index-attr-name')
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }]
        },
        'notification': {
            'httpCustom': {
                'url': 'http://ql/notify',
                'headers': {
                    TIME_INDEX_HEADER_NAME: 'my-time-index-attr-name'
                }
            },
            'metadata': ['dateCreated', 'dateModified', 'TimeInstant',
                         'timestamp', 'my-time-index-attr-name']
        },
        'throttling': 1
    }

    assert actual == expected


'''
subscription tests
'''


@pytest.mark.skip("deprecated")
def test_invalid_wrong_orion_url(clean_mongo, clean_crate):
    params = {
        'orionUrl': "blabla",
        'quantumleapUrl': "quantumleap",
    }
    r = requests.post(subscribe_url, params=params)
    assert r.status_code == 400
    assert r.json() == {
        "error": "Bad Request",
        "description": "Orion is not reachable at blabla"
    }


@pytest.mark.skip("deprecated")
def test_valid_defaults(clean_mongo, clean_crate):
    params = {
        'orionUrl': ORION_URL_4QL,
        'quantumleapUrl': QL_URL_4ORION,
    }
    r = requests.post(subscribe_url, params=params)
    assert r.status_code == 201

    # Check created subscription
    r = requests.get("{}/subscriptions".format(ORION_URL))
    assert r.ok
    res = r.json()
    assert len(res) == 1
    subscription = res[0]

    assert subscription['description'] == 'Created by QuantumLeap {}.' \
                                          ''.format(QL_URL_4ORION)
    assert subscription['subject'] == {
        'entities': [{'idPattern': '.*'}],
        'condition': {'attrs': []}
    }
    assert subscription['notification'] == {
        'attrs': [],
        'attrsFormat': 'normalized',
        'http': {'url': "{}/notify".format(QL_URL_4ORION)},
        'metadata': ['dateCreated', 'dateModified', 'TimeInstant', 'timestamp']
    }
    assert subscription['throttling'] == 1


@pytest.mark.skip("deprecated")
def test_valid_customs(clean_mongo, clean_crate):
    headers = {
        'Fiware-Service': 'custom',
        'Fiware-ServicePath': '/custom',
    }
    params = {
        'orionUrl': ORION_URL_4QL,
        'quantumleapUrl': QL_URL_4ORION,
        'entityType': "Room",
        'idPattern': "Room1",
        'observedAttributes': "temperature,pressure",
        'notifiedAttributes': "pressure",
        'throttling': 30
    }
    r = requests.post(subscribe_url, params=params, headers=headers)
    assert r.status_code == 201

    # Check created subscription
    r = requests.get("{}/subscriptions".format(ORION_URL), headers=headers)
    assert r.ok
    res = r.json()
    assert len(res) == 1
    subscription = res[0]

    description = 'Created by QuantumLeap {}.'.format(QL_URL_4ORION)
    assert subscription['description'] == description
    assert subscription['subject'] == {
        'entities': [{'idPattern': 'Room1', 'type': 'Room'}],
        'condition': {'attrs': ["temperature", "pressure"]}
    }
    assert subscription['notification'] == {
        'attrs': ["pressure"],
        'attrsFormat': 'normalized',
        'http': {'url': "{}/notify".format(QL_URL_4ORION)},
        'metadata': ['dateCreated', 'dateModified', 'TimeInstant', 'timestamp']
    }
    assert subscription['throttling'] == 30


@pytest.mark.skip("deprecated")
def test_use_multitenancy_headers(clean_mongo, clean_crate):
    headers = {
        'Fiware-Service': 'used',
        'Fiware-ServicePath': '/custom/from/headers',
    }
    params = {
        'orionUrl': ORION_URL_4QL,
        'quantumleapUrl': QL_URL_4ORION,
        'entityType': "Room",
        'idPattern': "Room1",
        'observedAttributes': "temperature,pressure",
    }
    # Post with FIWARE headers
    r = requests.post(subscribe_url, params=params, headers=headers)
    assert r.status_code == 201

    # Check created subscription using headers via http headers
    headers = {
        'fiware-service': "used",
        'fiware-servicepath': "/custom/from/headers",
    }
    r = requests.get("{}/subscriptions".format(ORION_URL), headers=headers)
    assert r.ok
    res = r.json()
    assert len(res) == 1

    # No headers no results
    r = requests.get("{}/subscriptions".format(ORION_URL), headers={})
    assert r.ok
    res = r.json()
    assert len(res) == 0


@pytest.mark.skip("deprecated")
def test_custom_time_index(clean_mongo, clean_crate):
    params = {
        'orionUrl': ORION_URL_4QL,
        'quantumleapUrl': QL_URL_4ORION,
        'entityType': 'Room',
        'idPattern': 'Room1',
        'observedAttributes': 'temperature,pressure',
        'notifiedAttributes': 'pressure',
        'timeIndexAttribute': 'my-time-index'
    }
    r = requests.post(subscribe_url, params=params)
    assert r.status_code == 201

    # Check created subscription
    r = requests.get("{}/subscriptions".format(ORION_URL))
    assert r.ok
    res = r.json()
    assert len(res) == 1
    subscription = res[0]

    description = 'Created by QuantumLeap {}.'.format(QL_URL_4ORION)
    assert subscription['description'] == description
    assert subscription['subject'] == {
        'entities': [{'idPattern': 'Room1', 'type': 'Room'}],
        'condition': {'attrs': ['temperature', 'pressure']}
    }
    assert subscription['notification'] == {
        'attrs': ['pressure'],
        'attrsFormat': 'normalized',
        'httpCustom': {
            'url': "{}/notify".format(QL_URL_4ORION),
            'headers': {
                TIME_INDEX_HEADER_NAME: 'my-time-index'
            }
        },
        'metadata': ['dateCreated', 'dateModified', 'TimeInstant', 'timestamp',
                     'my-time-index']
    }
