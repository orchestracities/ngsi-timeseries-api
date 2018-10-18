from conftest import QL_URL, crate_translator as translator
from datetime import datetime
from reporter.tests.utils import insert_test_data
import pytest
import requests

entity_type = 'Room'
attr_name = 'temperature'
n_days = 6


def query_url(values=False):
    url = "{qlUrl}/types/{entityType}/attrs/{attrName}"
    if values:
        url += '/value'
    return url.format(
        qlUrl=QL_URL,
        entityType=entity_type,
        attrName=attr_name,
    )


@pytest.fixture()
def reporter_dataset(translator):
    insert_test_data(translator,
                     [entity_type],
                     n_entities=3,
                     n_days=n_days)
    yield


def test_1TNE1A_defaults(reporter_dataset):
    # Query without specific id
    query_params = {
        'type': entity_type,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    expected_entities = [
        {
            'entityId': 'Room0',
            'index': expected_index,
            'values': expected_values,
        },
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_values,
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_values,
        }
    ]

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)
    assert obtained_data['data']['entityType'] == entity_type
    assert obtained_data['data']['attrName'] == attr_name
    assert obtained_data['data']['entities'] == expected_entities


def test_1TNE1A_one_entity(reporter_dataset):
    # Query
    entity_id = 'Room1'
    query_params = {
        'type': entity_type,
        'id': entity_id
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)

    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_values,
        }
    ]
    assert obtained_data['data']['entityType'] == entity_type
    assert obtained_data['data']['attrName'] == attr_name
    assert obtained_data['data']['entities'] == expected_entities


def test_1TNE1A_some_entities(reporter_dataset):
    # Query
    entity_id = 'Room0,Room2'
    query_params = {
        'type': entity_type,
        'id': entity_id
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    expected_entities = [
        {
            'entityId': 'Room0',
            'index': expected_index,
            'values': expected_values,
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_values,
        }
    ]

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)
    assert obtained_data['data']['entityType'] == entity_type
    assert obtained_data['data']['attrName'] == attr_name
    assert obtained_data['data']['entities'] == expected_entities


def test_1TNE1A_values_defaults(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'id': 'Room0,,Room1,RoomNotValid',  # -> validates to Room0,Room1.
    }
    r = requests.get(query_url(values=True), params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    expected_entities = [
        {
            'entityId': 'Room0',
            'index': expected_index,
            'values': expected_values,
        },
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_values,
        }
    ]

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)
    assert obtained_data == {'data': {'values': expected_entities}}


def test_not_found():
    query_params = {
        'type': entity_type,
        'id': 'RoomNotValid'
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


def test_weird_ids(reporter_dataset):
    """
    Invalid ids are ignored (provided at least one is valid to avoid 404).
    Empty values are ignored.
    Order of ids is preserved in response (e.g., Room1 first, Room0 later)
    """
    query_params = {
        'type': entity_type,
        'id': 'Room1,RoomNotValid,,Room0,',  # -> validates to Room0,Room1.
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_values,
        },
        {
            'entityId': 'Room0',
            'index': expected_index,
            'values': expected_values,
        }
    ]

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)
    assert obtained_data['data']['entityType'] == entity_type
    assert obtained_data['data']['attrName'] == attr_name
    assert obtained_data['data']['entities'] == expected_entities


def test_different_time_indexes(translator):
    """
    Each entity should have its time_index array.
    """
    t = 'Room'
    insert_test_data(translator, [t], n_entities=1, entity_id='Room1', n_days=2)
    insert_test_data(translator, [t], n_entities=1, entity_id='Room3', n_days=4)
    insert_test_data(translator, [t], n_entities=1, entity_id='Room2', n_days=3)

    query_params = {
        'type': 'Room',
        'id': 'Room3,Room1,Room2',
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    expected_entities = [
        {
            'entityId': 'Room3',
            'index': ['1970-01-{:02}T00:00:00'.format(i+1) for i in range(4)],
            'values': list(range(4)),
        },
        {
            'entityId': 'Room1',
            'index': ['1970-01-{:02}T00:00:00'.format(i+1) for i in range(2)],
            'values': list(range(2)),
        },
        {
            'entityId': 'Room2',
            'index': ['1970-01-{:02}T00:00:00'.format(i+1) for i in range(3)],
            'values': list(range(3)),
        }
    ]

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)
    assert obtained_data['data']['entityType'] == 'Room'
    assert obtained_data['data']['attrName'] == attr_name
    assert obtained_data['data']['entities'] == expected_entities


def test_aggregation_is_per_instance(translator):
    """
    Attribute Aggregation works by default on a per-instance basis.
    Cross-instance aggregation not yet supported.
    It would change the shape of the response.
    """
    t = 'Room'
    insert_test_data(translator, [t], n_entities=1, entity_id='Room0', n_days=3)
    insert_test_data(translator, [t], n_entities=1, entity_id='Room1', n_days=9)

    query_params = {
        'type': t,
        'id': 'Room0,Room1',
        'aggrMethod': 'sum'
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_entities = [
        {
            'entityId': 'Room0',
            'index': ['', ''],
            'values': [sum(range(3))],
        },
        {
            'entityId': 'Room1',
            'index': ['', ''],
            'values': [sum(range(9))],
        }
    ]

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)
    assert obtained_data['data']['entityType'] == t
    assert obtained_data['data']['attrName'] == attr_name
    assert obtained_data['data']['entities'] == expected_entities

    # Index array in the response is the used fromDate and toDate
    query_params = {
        'type': t,
        'id': 'Room0,Room1',
        'aggrMethod': 'max',
        'fromDate': datetime(1970, 1, 1).isoformat(),
        'toDate': datetime(1970, 1, 6).isoformat(),
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_entities = [
        {
            'entityId': 'Room0',
            'index': ['1970-01-01T00:00:00', '1970-01-06T00:00:00'],
            'values': [2],
        },
        {
            'entityId': 'Room1',
            'index': ['1970-01-01T00:00:00', '1970-01-06T00:00:00'],
            'values': [5],
        }
    ]

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)
    assert obtained_data['data']['entityType'] == t
    assert obtained_data['data']['attrName'] == attr_name
    assert obtained_data['data']['entities'] == expected_entities


def test_1T1ENA_aggrPeriod(reporter_dataset):
    # GH issue https://github.com/smartsdk/ngsi-timeseries-api/issues/89

    # aggrPeriod needs aggrMethod
    query_params = {
        'type': entity_type,
        'aggrPeriod': 'minute',
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 400, r.text

    query_params = {
        'type': entity_type,
        'aggrMethod': 'avg',
        'aggrPeriod': 'minute',
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 501, r.text
