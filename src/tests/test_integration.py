import time

from tests.common import load_data, check_data, unload_data, \
    check_deleted_data, QL_URL_4ORION
from reporter.tests.utils import delete_entity_type
from conftest import *


def notify_header(service=None, service_path=None):
    return headers(service, service_path, True)


def query_header(service=None, service_path=None):
    return headers(service, service_path, False)


notify_url = "{}/v2/notify".format(QL_URL_4ORION)

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
        entities = load_data(old=False, entity_type="TestEntity")
        assert len(entities) > 1
        # sleep should not be needed now since we have a retries in
        # check_data...
        time.sleep(10)
        check_data(entities, False)
    finally:
        unload_data(entities)
        check_deleted_data(entities)


def do_integration(entity, subscription, orion_client, service=None,
                   service_path=None):

    try:
        subscription_id = orion_client.subscribe(subscription, service,
                                                 service_path). \
            headers['Location'][18:]
        time.sleep(1)
        orion_client.insert(entity, service, service_path)
        entities_url = "{}/entities".format(QL_URL)

        h = headers(
            service=service,
            service_path=service_path,
            content_type=False)
        r = None
        for t in range(30):
            r = requests.get(entities_url, params=None, headers=h)
            if r.status_code == 200:
                break
            else:
                time.sleep(1)
        assert r.status_code == 200
        entities = r.json()
        assert len(entities) == 1

        assert entities[0]['entityId'] == entity['id']
        assert entities[0]['entityType'] == entity['type']
    finally:
        delete_entity_type(service, entity['type'], None)
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
