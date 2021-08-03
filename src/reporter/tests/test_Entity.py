from conftest import QL_URL
from reporter.tests.utils import insert_test_data, delete_test_data
import pytest
import requests
from utils.tests.common import assert_equal_time_index_arrays
import dateutil.parser

entity_type = 'Room'
entity_id = 'Room0'
temperature = 'temperature'
pressure = 'pressure'
n_days = 30
services = ['t1', 't2']


def query_url(eid=entity_id):
    url = "{qlUrl}/{entityId}"
    return url.format(
        qlUrl=QL_URL,
        entityId=eid,
    )


@pytest.fixture(scope='module')
def reporter_dataset():
    for service in services:
        insert_test_data(service, [entity_type], n_entities=1, index_size=30)
    yield
    for service in services:
        delete_test_data(service, [entity_type])


def assert_Entity_response(obtained, expected):
    """
    Check API responses for Entity
    """
    # Assert time index
    obt_index = obtained.pop('index')
    exp_index = expected.pop('index')
    assert_equal_time_index_arrays(obt_index, exp_index)

    # Assert rest of data
    assert obtained == expected

#Test for API without any query parameter
@pytest.mark.parametrize("service", services)
def test_Entity_defaults(service, reporter_dataset):
    query_params = {}
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': ['1970-01-30T00:00:00+00:00'],
        'attributes': [
            {
                'attrName': pressure,
                'values': [290.0],
            },
            {
                'attrName': temperature,
                'values': [29.0],
            }
        ]
    }
    obtained = r.json()
    assert_Entity_response(obtained, expected)

# Test API with type as query parameter
@pytest.mark.parametrize("service", services)
def test_Entity_type(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': ['1970-01-30T00:00:00+00:00'],
        'attributes': [
            {
                'attrName': pressure,
                'values': [290.0],
            },
            {
                'attrName': temperature,
                'values': [29.0],
            }
        ]
    }
    obtained = r.json()
    assert_Entity_response(obtained, expected)

#Test API for attrs as query parameter
@pytest.mark.parametrize("service", services)
def test_Entity_attrs(service, reporter_dataset):
    # Query
    query_params = {
        'attrs': 'temperature'
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': ['1970-01-30T00:00:00+00:00'],
        'attributes': [
            {
                'attrName': temperature,
                'values': [29.0]
            }
        ]
    }
    obtained = r.json()
    assert_Entity_response(obtained, expected)

#Test API for all the query parameter
@pytest.mark.parametrize("service", services)
def test_Entity_combined(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'attrs': 'temperature'
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': ['1970-01-30T00:00:00+00:00'],
        'attributes': [
            {
                'attrName': temperature,
                'values': [29.0]
            }
        ]
    }
    obtained = r.json()
    assert_Entity_response(obtained, expected)

# Test API for non-existing enity Id
@pytest.mark.parametrize("service", services)
def test_not_found(service):
    query_params = {}
    h = {'Fiware-Service': service}

    r = requests.get(query_url('Kitchen0'), params=query_params, headers=h)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }

# Test API for different Fiware-Service
def test_different_service():
    query_params = {}
    h = {'Fiware-Service': 't3'}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }

# Test API for different Fiware-ServicePath
@pytest.mark.parametrize("service", services)
def test_different_service_path(service):
    query_params = {}
    h = {'Fiware-Service': service,'Fiware-ServicePath':'/test'}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }
