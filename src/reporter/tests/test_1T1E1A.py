from conftest import QL_URL
from reporter.tests.utils import insert_test_data
from conftest import crate_translator as translator
import pytest
import requests

entity_type = 'Room'
entity_id = 'Room0'
attr_name = 'temperature'
n_days = 30


def query_url(values=False):
    url = "{qlUrl}/entities/{entityId}/attrs/{attrName}"
    if values:
        url += '/value'
    return url.format(
        qlUrl=QL_URL,
        entityId=entity_id,
        attrName=attr_name,
    )


@pytest.fixture()
def reporter_dataset(translator):
    insert_test_data(translator,
                     [entity_type],
                     n_entities=1,
                     n_days=30)
    yield


def test_1T1E1A_defaults(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Assert
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    expected_data = {
        'data': {
            'entityId': entity_id,
            'attrName': attr_name,
            'index': expected_index,
            'values': expected_values,
        }
    }
    assert r.json() == expected_data


@pytest.mark.parametrize("aggr_method, aggr_value", [
    ("count", 30),
    ("sum", 435),
    ("avg", 14.5),
    ("min", 0),
    ("max", 29),
])
def test_1T1E1A_aggrMethod(reporter_dataset, aggr_method, aggr_value):
    # Query
    query_params = {
        'type': entity_type,
        'aggrMethod': aggr_method,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Assert
    expected_data = {
        'data': {
            'entityId': entity_id,
            'attrName': attr_name,
            'index': [],
            'values': [aggr_value],
        }
    }
    assert r.json() == expected_data


def test_1T1E1A_fromDate_toDate(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'fromDate': "1970-01-06T00:00:00",
        'toDate': "1970-01-17T00:00:00",
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_values = list(range(5, 17))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    assert len(expected_index) == 12
    assert expected_index[0] == "1970-01-06T00:00:00"
    assert expected_index[-1] == "1970-01-17T00:00:00"

    # Assert
    expected_data = {
        'data': {
            'entityId': entity_id,
            'attrName': attr_name,
            'index': expected_index,
            'values': expected_values,
        }
    }
    assert r.json() == expected_data


def test_1T1E1A_lastN(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'lastN': 10
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_values = list(range(n_days-10, n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    assert len(expected_index) == 10
    assert expected_index[0] == "1970-01-21T00:00:00"
    assert expected_index[-1] == "1970-01-30T00:00:00"

    # Assert
    expected_data = {
        'data': {
            'entityId': entity_id,
            'attrName': attr_name,
            'index': expected_index,
            'values': expected_values,
        }
    }
    assert r.json() == expected_data


def test_1T1E1A_limit(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'limit': 5
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_values = list(range(5))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    assert len(expected_index) == 5
    assert expected_index[0] == "1970-01-01T00:00:00"
    assert expected_index[-1] == "1970-01-05T00:00:00"

    # Assert
    expected_data = {
        'data': {
            'entityId': entity_id,
            'attrName': attr_name,
            'index': expected_index,
            'values': expected_values,
        }
    }
    assert r.json() == expected_data


def test_1T1E1A_offset(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'offset': 3
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_values = list(range(3, n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    assert len(expected_index) == 27
    assert expected_index[0] == "1970-01-04T00:00:00"
    assert expected_index[-1] == "1970-01-30T00:00:00"

    # Assert
    expected_data = {
        'data': {
            'entityId': entity_id,
            'attrName': attr_name,
            'index': expected_index,
            'values': expected_values,
        }
    }
    assert r.json() == expected_data


def test_1T1E1A_combined(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'offset': 2,
        'toDate': "1970-01-20T00:00:00",
        'limit': 28,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_values = list(range(2, 20))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    assert len(expected_index) == 18
    assert expected_index[0] == "1970-01-03T00:00:00"
    assert expected_index[-1] == "1970-01-20T00:00:00"

    # Assert
    expected_data = {
        'data': {
            'entityId': entity_id,
            'attrName': attr_name,
            'index': expected_index,
            'values': expected_values,
        }
    }
    assert r.json() == expected_data


def test_1T1E1A_values_defaults(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
    }
    r = requests.get(query_url(values=True), params=query_params)
    assert r.status_code == 200, r.text

    # Assert
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    expected_data = {
        'data': {
            'index': expected_index,
            'values': expected_values,
        }
    }
    assert r.json() == expected_data


def test_not_found():
    query_params = {
        'type': entity_type,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


def test_tmp_no_type():
    """
    For now specifying entity type is mandatory
    """
    r = requests.get(query_url(), params={})
    assert r.status_code == 400, r.text
    assert r.json() == {
        "error": "Not Implemented",
        "description": "For now, you must always specify entity type."
    }
