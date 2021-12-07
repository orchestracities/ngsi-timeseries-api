from conftest import QL_URL
from exceptions.exceptions import AmbiguousNGSIIdError
from reporter.tests.utils import insert_test_data, delete_test_data, \
    wait_for_insert
from utils.tests.common import assert_equal_time_index_arrays
import dateutil.parser
import pytest
import requests

entity_type = 'Room'
entity_id = 'Room0'
attr_name = 'temperature'
n_days = 30
services = ['t1', 't2']


def query_url(entity_type='Room', eid='Room0', values=False):
    url = "{qlUrl}/entities/{entityId}/attrs/{attrName}"
    if values:
        url += '/value'
    return url.format(
        qlUrl=QL_URL,
        entityId=eid,
        attrName=attr_name,
    )


@pytest.fixture(scope='module')
def reporter_dataset():
    for service in services:
        insert_test_data(service, [entity_type], n_entities=1, index_size=30)
    yield
    for service in services:
        delete_test_data(service, [entity_type])


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


@pytest.mark.parametrize("service", services)
def test_1T1E1A_defaults(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    obtained = r.json()

    exp_values = list(range(n_days))
    exp_index = [
        '1970-01-{:02}T00:00:00.00+00:00'.format(i + 1) for i in exp_values
    ]
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
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
@pytest.mark.parametrize("service", services)
def test_1T1E1A_aggrMethod(service, reporter_dataset, aggr_method, aggr_value):
    # Query
    query_params = {
        'type': entity_type,
        'aggrMethod': aggr_method,
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'attrName': attr_name,
        'index': [],
        'values': [aggr_value]
    }
    assert_1T1E1A_response(obtained, expected)


@pytest.mark.parametrize("aggr_period, exp_index, ins_period", [
    ("year", ['1970-01-01T00:00:00.000+00:00',
              '1971-01-01T00:00:00.000+00:00',
              '1972-01-01T00:00:00.000+00:00'], "month"),
    ("day", ['1970-01-01T00:00:00.000+00:00',
             '1970-01-02T00:00:00.000+00:00',
             '1970-01-03T00:00:00.000+00:00'], "hour"),
    ("second", ['1970-01-01T00:00:00.000+00:00',
                '1970-01-01T00:00:01.000+00:00',
                '1970-01-01T00:00:02.000+00:00'], "milli"),
])
@pytest.mark.parametrize("service", services)
def test_1T1E1A_aggrPeriod(service, aggr_period, exp_index, ins_period):
    etype = f"test_1T1E1A_aggrPeriod_{aggr_period}"
    # The reporter_dataset fixture is still in the DB cos it has a scope of
    # module. We use a different entity type to store this test's rows in a
    # different table to avoid messing up global state---see also delete down
    # below.
    eid = "{}0".format(etype)

    # Custom index to test aggrPeriod
    for i in exp_index:
        base = dateutil.parser.isoparse(i)
        insert_test_data(service,
                         [etype],
                         entity_id=eid,
                         index_size=4,
                         index_base=base,
                         index_period=ins_period)

    wait_for_insert([etype], service, 4 * len(exp_index))

    # aggrPeriod needs aggrMethod
    query_params = {
        'type': etype,
        'aggrPeriod': aggr_period,
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(eid=eid), params=query_params, headers=h)
    assert r.status_code == 400, r.text

    # Check aggregation with aggrPeriod
    query_params = {
        'type': etype,
        'aggrMethod': 'avg',
        'aggrPeriod': aggr_period,
    }
    r = requests.get(query_url(eid=eid), params=query_params, headers=h)

    delete_test_data(service, [etype])

    assert r.status_code == 200, r.text

    # Assert Results
    obtained = r.json()
    exp_avg = (0 + 1 + 2 + 3) / 4.
    expected = {
        'entityId': eid,
        'entityType': etype,
        'attrName': attr_name,
        'index': exp_index,
        'values': [exp_avg, exp_avg, exp_avg]
    }
    assert_1T1E1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1E1A_fromDate_toDate(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'fromDate': "1970-01-06T00:00:00+00:00",
        'toDate': "1970-01-17T00:00:00+00:00",
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_values = list(range(5, 17))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
    ]
    assert len(expected_index) == 12
    assert expected_index[0] == "1970-01-06T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-17T00:00:00+00:00"

    # Assert
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attrName': attr_name,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1E1A_fromDate_toDate_with_quotes(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'fromDate': '"1970-01-06T00:00:00+00:00"',
        'toDate': '"1970-01-17T00:00:00+00:00"',
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_values = list(range(5, 17))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
    ]
    assert len(expected_index) == 12
    assert expected_index[0] == "1970-01-06T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-17T00:00:00+00:00"

    # Assert
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attrName': attr_name,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1E1A_lastN(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'lastN': 10
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_values = list(range(n_days - 10, n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
    ]
    assert len(expected_index) == 10
    assert expected_index[0] == "1970-01-21T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-30T00:00:00+00:00"

    # Assert
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'attrName': attr_name,
        'index': expected_index,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1E1A_lastN_with_limit(service, reporter_dataset):
    """
    See GitHub issue #249.
    """
    # Query
    query_params = {
        'type': entity_type,
        'lastN': 3,
        'limit': 10
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_temperatures = [27, 28, 29]
    expected_index = [
        '1970-01-28T00:00:00+00:00',
        '1970-01-29T00:00:00+00:00',
        '1970-01-30T00:00:00+00:00'
    ]

    # Assert
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'attrName': attr_name,
        'index': expected_index,
        'values': expected_temperatures
    }
    assert_1T1E1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1E1A_limit(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'limit': 5
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_values = list(range(5))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
    ]
    assert len(expected_index) == 5
    assert expected_index[0] == "1970-01-01T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-05T00:00:00+00:00"

    # Assert
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'attrName': attr_name,
        'index': expected_index,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1E1A_offset(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'offset': 3
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_values = list(range(3, n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
    ]
    assert len(expected_index) == 27
    assert expected_index[0] == "1970-01-04T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-30T00:00:00+00:00"

    # Assert
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'attrName': attr_name,
        'index': expected_index,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1E1A_combined(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'offset': 2,
        'toDate': "1970-01-20T00:00:00+00:00",
        'limit': 28,
    }

    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_values = list(range(2, 20))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
    ]
    assert len(expected_index) == 18
    assert expected_index[0] == "1970-01-03T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-20T00:00:00+00:00"

    # Assert
    obtained = r.json()
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'attrName': attr_name,
        'index': expected_index,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1E1A_values_defaults(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
    }

    h = {'Fiware-Service': service}

    r = requests.get(query_url(values=True), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert
    obtained = r.json()
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
    ]
    expected = {
        'index': expected_index,
        'values': expected_values
    }
    assert_1T1E1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_not_found(service):
    query_params = {
        'type': 'NotThere',
    }

    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


@pytest.mark.parametrize("service", services)
def test_no_type(service):
    """
    Specifying entity type is optional, provided that id is unique.
    """

    etype_1, etype_2 = 'test_no_type_RoomDevice', 'test_no_type_Car'
    etypes = [etype_1, etype_2]
    eid = "{}1".format(etype_1)
    # The reporter_dataset fixture is still in the DB cos it has a scope of
    # module. We use different entity types to store this test's rows in
    # different tables to avoid messing up global state---see also delete
    # down below.
    insert_test_data(service, etypes, n_entities=2, index_size=2)
    wait_for_insert(etypes, service, 2 * 2)

    h = {'Fiware-Service': service}

    # With type
    r = requests.get(query_url(eid=eid), params={'type': etype_1}, headers=h)
    assert r.status_code == 200, r.text
    res_with_type = r.json()

    # Without type
    r = requests.get(query_url(eid=eid), params={}, headers=h)
    assert r.status_code == 200, r.text
    res_without_type = r.json()

    assert res_with_type == res_without_type
    delete_test_data(service, etypes)


@pytest.mark.parametrize("service", services)
def test_no_type_not_unique(service):
    # If id is not unique across types, you must specify type.

    etype_1, etype_2 = 'test_no_type_not_unique_RoomDevice', \
                       'test_no_type_not_unique_Car'
    etypes = [etype_1, etype_2]
    # The reporter_dataset fixture is still in the DB cos it has a scope of
    # module. We use different entity types to store this test's rows in
    # different tables to avoid messing up global state---see also delete
    # down below.
    shared_entity_id = "sharedId"

    insert_test_data(service,
                     etypes,
                     n_entities=2,
                     index_size=2,
                     entity_id=shared_entity_id)
    wait_for_insert(etypes, service, 2 * 2)

    url = "{qlUrl}/entities/{entityId}/attrs/temperature".format(
        qlUrl=QL_URL,
        entityId=shared_entity_id,
    )

    h = {'Fiware-Service': service}

    # With type
    r = requests.get(url, params={'type': etype_1}, headers=h)
    assert r.status_code == 200, r.text

    # Without type
    r = requests.get(url, params={}, headers=h)
    assert r.status_code == 400, r.text
    e = AmbiguousNGSIIdError(shared_entity_id)
    assert r.json() == {
        "error": "{}".format(type(e)),
        "description": str(e)
    }
    delete_test_data(service, etypes)
