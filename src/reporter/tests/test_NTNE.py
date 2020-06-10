from conftest import QL_URL
from reporter.tests.utils import insert_test_data, delete_test_data
from datetime import datetime
import pytest
import requests

entity_type = 'Room'
entity_type_1 = 'Kitchen'
entity_id = 'Room0'
entity_id_1 = 'Kitchen0'
n_days = 30


def query_url():
    url = "{qlUrl}/entities"
    return url.format(
        qlUrl=QL_URL
    )


@pytest.fixture(scope='module')
def reporter_dataset():
    service = ''
    insert_test_data(service, [entity_type], n_entities=1, index_size=30,
                     entity_id=entity_id)
    insert_test_data(service, [entity_type_1], n_entities=1, index_size=30,
                     entity_id=entity_id_1,
                     index_base=datetime(1980, 1, 1, 0, 0, 0, 0))
    yield
    delete_test_data(service, [entity_type, entity_type_1])


# TODO we removed order comparison given that in
# CRATE4.0 union all and order by don't work correctly with offset
def test_NTNE_defaults(reporter_dataset):
    r = requests.get(query_url())
    assert r.status_code == 200, r.text

    obtained = r.json()
    expected = [{
        "id": 'Kitchen0',
        "index": [
            "1980-01-30T00:00:00.000+00:00"
        ],
        "type": 'Kitchen'
    }, {
        "id": 'Room0',
        "index": [
            "1970-01-30T00:00:00.000+00:00"
        ],
        "type": 'Room'
    }]

    assert obtained == expected


def test_not_found():
    query_params = {
        'type': 'NotThere'
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


def test_NTNE_type(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Assert
    obtained = r.json()
    expected_type = 'Room'
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_values
    ]
    expected = [{
        'id': 'Room0',
        'index': [expected_index[-1]],
        'type': expected_type
    }]
    assert obtained == expected


# TODO we removed order comparison given that in
# CRATE4.0 union all and order by don't work correctly with offset
def test_NTNE_fromDate_toDate(reporter_dataset):
    # Query
    query_params = {
        'fromDate': "1970-01-06T00:00:00+00:00",
        'toDate': "1980-01-17T00:00:00+00:00",
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text
    
    expected_type = 'Room'
    expected_id = 'Room0'
    expected_index = [
        '1970-01-30T00:00:00.000+00:00'
    ]
    expected_type_1 = 'Kitchen'
    expected_id_1 = 'Kitchen0'
    expected_index_1 = [
        '1980-01-17T00:00:00.000+00:00'
    ]

    # Assert
    obtained = r.json()
    expected = [{
        'id': expected_id_1,
        'index': expected_index_1,
        'type': expected_type_1
    }, {
        'id': expected_id,
        'index': expected_index,
        'type': expected_type
    }]
    assert obtained == expected


def test_NTNE_fromDate_toDate_with_quotes(reporter_dataset):
    # Query
    query_params = {
        'fromDate': '"1970-01-06T00:00:00+00:00"',
        'toDate': '"1980-01-17T00:00:00+00:00"',
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text
    
    expected_type = 'Room'
    expected_id = 'Room0'
    expected_index = [
        '1970-01-30T00:00:00.000+00:00'
    ]
    expected_type_1 = 'Kitchen'
    expected_id_1 = 'Kitchen0'
    expected_index_1 = [
        '1980-01-17T00:00:00.000+00:00'
    ]

    # Assert
    obtained = r.json()
    expected = [{
        'id': expected_id_1,
        'index': expected_index_1,
        'type': expected_type_1
    }, {
        'id': expected_id,
        'index': expected_index,
        'type': expected_type
    }]
    assert obtained == expected


# TODO we removed order comparison given that in
# CRATE4.0 union all and order by don't work correctly with offset
def test_NTNE_limit(reporter_dataset):
    # Query
    query_params = {
        'limit': 1
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    expected_type = 'Kitchen'
    expected_id = 'Kitchen0'
    expected_index = [
        '1980-01-30T00:00:00.000+00:00'
    ]

    # Assert
    obtained = r.json()
    expected = [{
        'id': expected_id,
        'index': expected_index,
        'type': expected_type
    }]
    assert len(obtained) == len(expected)


# TODO we removed order comparison given that in
# CRATE4.0 union all and order by don't work correctly with offset
def test_NTNE_offset(reporter_dataset):
    # Query
    query_params = {
        'offset': 1
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    expected_type = 'Kitchen'
    expected_id = 'Kitchen0'
    expected_index = [
        '1980-01-30T00:00:00.000+00:00'
    ]

    # Assert
    obtained = r.json()
    expected = [{
        'id': expected_id,
        'index': expected_index,
        'type': expected_type
    }]
    assert len(obtained) == len(expected)


def test_NTNE_combined(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'offset': 0,
        'fromDate': "1970-01-06T00:00:00+00:00",
        'toDate': "1980-01-20T00:00:00+00:00",
        'limit': 1,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text
    
    expected_type = 'Room'
    expected_id = 'Room0'
    expected_index = [
        '1970-01-30T00:00:00.000+00:00'
    ]

    # Assert
    obtained = r.json()
    expected = [{
        'id': expected_id,
        'index': expected_index,
        'type': expected_type
    }]
    assert obtained == expected
