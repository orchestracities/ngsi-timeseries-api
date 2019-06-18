from conftest import QL_URL, crate_translator as translator
from datetime import datetime
from exceptions.exceptions import AmbiguousNGSIIdError
from reporter.tests.utils import insert_test_data
from utils.common import assert_equal_time_index_arrays
import pytest
import requests

entity_type = 'Room'
entity_id = 'Room0'
attr_name = 'temperature'
n_days = 30


def query_url(entity_type='Room', entity_id='Room0', values=False):
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
    insert_test_data(translator, [entity_type], n_entities=1, index_size=30)
    yield


def assert_1T1E1A_response(obtained, expected):
    """
    Check API responses for 1T1E1A
    """
    # Assert time index
    obt_index = obtained.pop('index')
    exp_index = expected.pop('index')
    assert_equal_time_index_arrays(obt_index, exp_index)

    # Assert rest of data
    assert obtained == expected


def test_1T1E1A_defaults(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    obtained = r.json()

    exp_values = list(range(n_days))
    exp_index = [
        '1970-01-{:02}T00:00:00.00'.format(i+1) for i in exp_values
    ]
    expected = {
        'entityId': entity_id,
        'attrName': attr_name,
        'index': exp_index,
        'values': exp_values
    }
    assert_1T1E1A_response(obtained, expected)


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

    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'attrName': attr_name,
        'index': [],
        'values': [aggr_value]
    }
    assert_1T1E1A_response(obtained, expected)


@pytest.mark.parametrize("aggr_period, exp_index, ins_period", [
    ("year", ['1970-01-01T00:00:00.000',
              '1971-01-01T00:00:00.000',
              '1972-01-01T00:00:00.000'], "month"),
    ("day",  ['1970-01-01T00:00:00.000',
              '1970-01-02T00:00:00.000',
              '1970-01-03T00:00:00.000'], "hour"),
    ("second", ['1970-01-01T00:00:00.000',
                '1970-01-01T00:00:01.000',
                '1970-01-01T00:00:02.000'], "milli"),
])
def test_1T1E1A_aggrPeriod(translator, aggr_period, exp_index, ins_period):
    # Custom index to test aggrPeriod
    for i in exp_index:
        base = datetime.strptime(i, "%Y-%m-%dT%H:%M:%S.%f")
        insert_test_data(translator,
                         [entity_type],
                         index_size=4,
                         index_base=base,
                         index_period=ins_period)

    # aggrPeriod needs aggrMethod
    query_params = {
        'type': entity_type,
        'aggrPeriod': aggr_period,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 400, r.text

    # Check aggregation with aggrPeriod
    query_params = {
        'type': entity_type,
        'aggrMethod': 'avg',
        'aggrPeriod': aggr_period,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    obtained = r.json()
    exp_avg = (0 + 1 + 2 + 3) / 4.
    expected = {
        'entityId': entity_id,
        'attrName': attr_name,
        'index': exp_index,
        'values': [exp_avg, exp_avg, exp_avg]
    }
    assert_1T1E1A_response(obtained, expected)


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
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'index': expected_index,
        'attrName': attr_name,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


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
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'attrName': attr_name,
        'index': expected_index,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


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
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'attrName': attr_name,
        'index': expected_index,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


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
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'attrName': attr_name,
        'index': expected_index,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


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
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'attrName': attr_name,
        'index': expected_index,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


def test_1T1E1A_values_defaults(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
    }
    r = requests.get(query_url(values=True), params=query_params)
    assert r.status_code == 200, r.text

    # Assert
    obtained = r.json()
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_values
    ]
    expected = {
        'index': expected_index,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


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


def test_no_type(translator):
    """
    Specifying entity type is optional, provided that id is unique.
    """
    insert_test_data(translator, ['Room', 'Car'], n_entities=2, index_size=30)

    # With type
    r = requests.get(query_url(), params={'type': 'Room'})
    assert r.status_code == 200, r.text
    res_with_type = r.json()

    # Without type
    r = requests.get(query_url(), params={})
    assert r.status_code == 200, r.text
    res_without_type = r.json()

    assert res_with_type == res_without_type


def test_no_type_not_unique(translator):
    # If id is not unique across types, you must specify type.
    insert_test_data(translator,
                     ['Room', 'Car'],
                     n_entities=2,
                     index_size=30,
                     entity_id="repeatedId")

    url = "{qlUrl}/entities/{entityId}/attrs/temperature".format(
        qlUrl=QL_URL,
        entityId="repeatedId",
    )

    # With type
    r = requests.get(url, params={'type': 'Room'})
    assert r.status_code == 200, r.text

    # Without type
    r = requests.get(url, params={})
    assert r.status_code == 409, r.text
    assert r.json() == {
        "error": "AmbiguousNGSIIdError",
        "description": str(AmbiguousNGSIIdError('repeatedId'))
    }
