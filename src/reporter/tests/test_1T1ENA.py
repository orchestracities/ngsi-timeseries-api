from conftest import QL_URL
from reporter.tests.utils import insert_test_data, delete_test_data, \
    wait_for_insert
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


def query_url(values=False, eid=entity_id):
    url = "{qlUrl}/entities/{entityId}"
    if values:
        url += '/value'
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


def assert_1T1ENA_response(obtained, expected):
    """
    Check API responses for 1T1ENA
    """
    # Assert time index
    obt_index = obtained.pop('index')
    exp_index = expected.pop('index')
    assert_equal_time_index_arrays(obt_index, exp_index)

    # Assert rest of data
    assert obtained == expected


@pytest.mark.parametrize("service", services)
def test_1T1ENA_defaults(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert
    expected_temperatures = list(range(n_days))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_temperatures
    ]
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': expected_pressures,
            },
            {
                'attrName': temperature,
                'values': expected_temperatures,
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)


@pytest.mark.parametrize("aggr_meth, aggr_press, aggr_temp", [
    ("count", 30, 30),
    ("sum", 4350, 435),
    ("avg", 145, 14.5),
    ("min", 0, 0),
    ("max", 290, 29),
])
@pytest.mark.parametrize("service", services)
def test_1T1ENA_aggrMethod(
        service,
        reporter_dataset,
        aggr_meth,
        aggr_press,
        aggr_temp):
    # attrs is compulsory when using aggrMethod
    query_params = {
        'type': entity_type,
        'aggrMethod': aggr_meth,
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 400, r.text

    # Query
    query_params = {
        'type': entity_type,
        'aggrMethod': aggr_meth,
        'attrs': temperature + ',' + pressure,
    }
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': [],
        'attributes': [
            {
                'attrName': pressure,
                'values': [aggr_press],
            },
            {
                'attrName': temperature,
                'values': [aggr_temp],
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)


@pytest.mark.parametrize("aggr_period, exp_index, ins_period", [
    ("month", ['1970-01-01T00:00:00.000+00:00',
               '1970-02-01T00:00:00.000+00:00',
               '1970-03-01T00:00:00.000+00:00'], "day"),
    ("hour", ['1970-01-01T00:00:00.000+00:00',
              '1970-01-01T01:00:00.000+00:00',
              '1970-01-01T02:00:00.000+00:00'], "minute"),
    ("minute", ['1970-01-01T00:00:00.000+00:00',
                '1970-01-01T00:01:00.000+00:00',
                '1970-01-01T00:02:00.000+00:00'], "second"),
])
@pytest.mark.parametrize("service", services)
def test_1T1ENA_aggrPeriod(service, aggr_period, exp_index, ins_period):
    # Custom index to test aggrPeriod

    etype = f"test_1T1ENA_aggrPeriod_{aggr_period}"
    # The reporter_dataset fixture is still in the DB cos it has a scope of
    # module. We use a different entity type to store this test's rows in a
    # different table to avoid messing up global state---see also delete down
    # below.
    eid = "{}0".format(etype)

    for i in exp_index:
        base = dateutil.parser.isoparse(i)
        insert_test_data(service,
                         [etype],
                         entity_id=eid,
                         index_size=3,
                         index_base=base,
                         index_period=ins_period)

    wait_for_insert([etype], service, 3 * len(exp_index))

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
        'attrs': temperature + ',' + pressure,
        'aggrMethod': 'max',
        'aggrPeriod': aggr_period,
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(eid=eid), params=query_params, headers=h)
    assert r.status_code == 200, r.text
    # Assert Results
    expected = {
        'entityId': eid,
        'entityType': etype,
        'index': exp_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': [20., 20., 20.],
            },
            {
                'attrName': temperature,
                'values': [2., 2., 2.],
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)
    delete_test_data(service, [etype])


@pytest.mark.parametrize("service", services)
def test_1T1ENA_fromDate_toDate(service, reporter_dataset):
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
    expected_temperatures = list(range(5, 17))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_temperatures
    ]
    assert len(expected_index) == 12
    assert expected_index[0] == "1970-01-06T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-17T00:00:00+00:00"

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': expected_pressures,
            },
            {
                'attrName': temperature,
                'values': expected_temperatures,
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1ENA_fromDate(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'fromDate': "1970-01-24T00:00:00+00:00"
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_temperatures = list(range(23, 30))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_temperatures
    ]
    assert len(expected_index) == 7
    assert expected_index[0] == "1970-01-24T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-30T00:00:00+00:00"

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': expected_pressures,
            },
            {
                'attrName': temperature,
                'values': expected_temperatures,
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)

# see #353


@pytest.mark.parametrize("service", services)
@pytest.mark.parametrize("last", [1, 3, 10, 10000])
def test_1T1ENA_fromDate_and_last(service, last, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'lastN': last,
        'fromDate': "1970-01-24T00:00:00+00:00"
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    max_range = 7
    if last < 7:
        max_range = last
    expected_temperatures = list(range(30 - max_range, 30))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_temperatures
    ]
    assert len(expected_index) == max_range

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': expected_pressures,
            },
            {
                'attrName': temperature,
                'values': expected_temperatures,
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1ENA_fromDate_toDate_with_quotes(service, reporter_dataset):
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
    expected_temperatures = list(range(5, 17))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_temperatures
    ]
    assert len(expected_index) == 12
    assert expected_index[0] == "1970-01-06T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-17T00:00:00+00:00"

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': expected_pressures,
            },
            {
                'attrName': temperature,
                'values': expected_temperatures,
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1ENA_lastN(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'lastN': 10
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_temperatures = list(range(n_days - 10, n_days))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_temperatures
    ]
    assert len(expected_index) == 10
    assert expected_index[0] == "1970-01-21T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-30T00:00:00+00:00"

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': expected_pressures,
            },
            {
                'attrName': temperature,
                'values': expected_temperatures,
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)


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

    # Expected
    expected_temperatures = [27, 28, 29]
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-28T00:00:00+00:00',
        '1970-01-29T00:00:00+00:00',
        '1970-01-30T00:00:00+00:00'
    ]
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': expected_pressures,
            },
            {
                'attrName': temperature,
                'values': expected_temperatures,
            }
        ]
    }

    # Assert
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1ENA_limit(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'limit': 5
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_temperatures = list(range(5))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_temperatures
    ]
    assert len(expected_index) == 5
    assert expected_index[0] == "1970-01-01T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-05T00:00:00+00:00"

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': expected_pressures,
            },
            {
                'attrName': temperature,
                'values': expected_temperatures,
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1ENA_offset(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'offset': 3
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Expect only last N
    expected_temperatures = list(range(3, n_days))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_temperatures
    ]
    assert len(expected_index) == 27
    assert expected_index[0] == "1970-01-04T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-30T00:00:00+00:00"

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': expected_pressures,
            },
            {
                'attrName': temperature,
                'values': expected_temperatures,
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1ENA_combined(service, reporter_dataset):
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
    expected_temperatures = list(range(2, 20))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_temperatures
    ]
    assert len(expected_index) == 18
    assert expected_index[0] == "1970-01-03T00:00:00+00:00"
    assert expected_index[-1] == "1970-01-20T00:00:00+00:00"

    # Assert
    expected = {
        'entityId': entity_id,
        'entityType': entity_type,
        'index': expected_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': expected_pressures,
            },
            {
                'attrName': temperature,
                'values': expected_temperatures,
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1T1ENA_values_defaults(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(values=True), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert
    expected_temperatures = list(range(n_days))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_temperatures
    ]
    expected = {
        'index': expected_index,
        'attributes': [
            {
                'attrName': pressure,
                'values': expected_pressures,
            },
            {
                'attrName': temperature,
                'values': expected_temperatures,
            }
        ]
    }
    obtained = r.json()
    assert_1T1ENA_response(obtained, expected)


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
