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
from conftest import QL_URL, ORION_URL, entity, clean_mongo
from reporter.tests.utils import delete_test_data
import json
import time
import requests
import pytest

services = ['t1', 't2']

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
        'orionUrl': ORION_URL,
        'quantumleapUrl': QL_URL,
    }
    r = requests.post("{}/subscribe".format(QL_URL), params=params, headers=h)
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
