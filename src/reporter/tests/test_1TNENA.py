from conftest import QL_URL
from datetime import datetime
from reporter.tests.utils import insert_test_data, delete_test_data, \
    wait_for_insert
from utils.tests.common import assert_equal_time_index_arrays
import pytest
import requests
import dateutil.parser

entity_type = 'Room'
attr_name_1 = 'temperature'
attr_name_2 = 'pressure'
n_days = 6
services = ['t1', 't2']

idPattern = "R"


def query_url(etype=entity_type, values=False):
    url = "{qlUrl}/types/{entityType}"
    if values:
        url += '/value'
    return url.format(
        qlUrl=QL_URL,
        entityType=etype
    )


@pytest.fixture(scope='module')
def reporter_dataset():
    for service in services:
        insert_test_data(service, [entity_type], n_entities=3,
                         index_size=n_days)
    yield
    for service in services:
        delete_test_data(service, [entity_type])


def assert_1TNENA_response(obtained, expected, etype=entity_type,
                           values_only=False):
    """
    Check API responses for 1TNENA
    """
    assert isinstance(obtained, dict)
    if not values_only:
        assert obtained['entityType'] == etype
        obt_entities_index = obtained['entities'][0]['index']
        exp_entities_index = expected['entities'][0]['index']
    else:
        obt_entities_index = obtained['values'][0]['index']
        exp_entities_index = expected['values'][0]['index']

    assert_equal_time_index_arrays(obt_entities_index, exp_entities_index)

    assert obtained == expected


@pytest.mark.parametrize("service", services)
def test_1TNENA_defaults(service, reporter_dataset):
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(n_days))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i + 1) for i in expected_temperatures
    ]
    expected_attributes = [
        {
            'attrName': attr_name_2,
            'values': expected_pressures
        },
        {
            'attrName': attr_name_1,
            'values': expected_temperatures
        }
    ]
    expected_entities = [
        {
            'attributes': expected_attributes,
            'entityId': 'Room0',
            'index': expected_index
        },
        {
            'attributes': expected_attributes,
            'entityId': 'Room1',
            'index': expected_index
        },
        {
            'attributes': expected_attributes,
            'entityId': 'Room2',
            'index': expected_index
        }
    ]
    expected = {
        'entities': expected_entities,
        'entityType': entity_type
    }

    obtained = r.json()
    assert_1TNENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1TNENA_idPattern(service, reporter_dataset):
    h = {'Fiware-Service': service}
    query_params = {'idPattern': idPattern}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(n_days))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i + 1) for i in expected_temperatures
    ]
    expected_attributes = [
        {
            'attrName': attr_name_2,
            'values': expected_pressures
        },
        {
            'attrName': attr_name_1,
            'values': expected_temperatures
        }
    ]
    expected_entities = [
        {
            'attributes': expected_attributes,
            'entityId': 'Room0',
            'index': expected_index
        },
        {
            'attributes': expected_attributes,
            'entityId': 'Room1',
            'index': expected_index
        },
        {
            'attributes': expected_attributes,
            'entityId': 'Room2',
            'index': expected_index
        }
    ]
    expected = {
        'entities': expected_entities,
        'entityType': entity_type
    }

    obtained = r.json()
    assert_1TNENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def idPattern_not_found(service):
    query_params = {
        'idPattern': 'roomNotFound'
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


@pytest.mark.parametrize("service", services)
def test_1TNENA_one_entity(service, reporter_dataset):
    # Query
    entity_id = 'Room1'
    query_params = {
        'id': entity_id
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)

    expected_temperatures = list(range(n_days))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i + 1) for i in expected_temperatures
    ]

    expected_attributes = [
        {
            'attrName': attr_name_2,
            'values': expected_pressures
        },
        {
            'attrName': attr_name_1,
            'values': expected_temperatures
        }
    ]

    expected_entities = [
        {
            'attributes': expected_attributes,
            'entityId': 'Room1',
            'index': expected_index
        }
    ]
    expected = {
        'entities': expected_entities,
        'entityType': entity_type
    }
    obtained = r.json()
    assert_1TNENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1TNENA_some_entities(service, reporter_dataset):
    # Query
    entity_id = 'Room0,Room2'
    query_params = {
        'id': entity_id
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(n_days))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i + 1) for i in expected_temperatures
    ]

    expected_attributes = [
        {
            'attrName': attr_name_2,
            'values': expected_pressures
        },
        {
            'attrName': attr_name_1,
            'values': expected_temperatures
        }
    ]

    expected_entities = [
        {
            'attributes': expected_attributes,
            'entityId': 'Room0',
            'index': expected_index
        },
        {
            'attributes': expected_attributes,
            'entityId': 'Room2',
            'index': expected_index
        },
    ]

    expected = {
        'entities': expected_entities,
        'entityType': entity_type
    }

    obtained = r.json()
    assert_1TNENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1TNENA_values_defaults(service, reporter_dataset):
    # Query
    query_params = {
        'id': 'Room0,,Room1,RoomNotValid',  # -> validates to Room0,Room1.
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(values=True), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(n_days))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i + 1) for i in expected_temperatures
    ]

    expected_attributes = [
        {
            'attrName': attr_name_2,
            'values': expected_pressures
        },
        {
            'attrName': attr_name_1,
            'values': expected_temperatures
        }
    ]

    expected_entities = [
        {
            'attributes': expected_attributes,
            'entityId': 'Room0',
            'index': expected_index
        },
        {
            'attributes': expected_attributes,
            'entityId': 'Room1',
            'index': expected_index
        },
    ]

    expected = {
        'values': expected_entities
    }

    obtained = r.json()
    assert_1TNENA_response(obtained, expected, values_only=True)


@pytest.mark.parametrize("service", services)
def test_not_found(service):
    query_params = {
        'id': 'RoomNotValid'
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


@pytest.mark.parametrize("service", services)
def test_weird_ids(service, reporter_dataset):
    """
    Invalid ids are ignored (provided at least one is valid to avoid 404).
    Empty values are ignored.
    Order of ids is preserved in response (e.g., Room1 first, Room0 later)
    """
    query_params = {
        'id': 'Room1,RoomNotValid,,Room0,',  # -> validates to Room0,Room1.
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(n_days))
    expected_pressures = [t * 10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i + 1) for i in expected_temperatures
    ]

    expected_attributes = [
        {
            'attrName': attr_name_2,
            'values': expected_pressures
        },
        {
            'attrName': attr_name_1,
            'values': expected_temperatures
        }
    ]

    expected_entities = [
        {
            'attributes': expected_attributes,
            'entityId': 'Room0',
            'index': expected_index
        },
        {
            'attributes': expected_attributes,
            'entityId': 'Room1',
            'index': expected_index
        },
    ]

    expected = {
        'entities': expected_entities,
        'entityType': entity_type
    }

    obtained = r.json()
    assert_1TNENA_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_aggregation_is_per_instance(service, reporter_dataset):
    """
    Attribute Aggregation works by default on a per-instance basis.
    Cross-instance aggregation not yet supported.
    It would change the shape of the response.
    """
    query_params = {
        'attrs': 'temperature',
        'id': 'Room0,Room1',
        'aggrMethod': 'sum'
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_attributes = [
        {
            'attrName': attr_name_1,
            'values': [sum(range(6))]
        }
    ]

    expected_entities = [
        {
            'attributes': expected_attributes,
            'entityId': 'Room0',
            'index': ['', '']
        },
        {
            'attributes': expected_attributes,
            'entityId': 'Room1',
            'index': ['', '']
        }
    ]

    expected = {
        'entities': expected_entities,
        'entityType': entity_type
    }

    obtained = r.json()
    assert isinstance(obtained, dict)
    assert obtained == expected

    # Index array in the response is the used fromDate and toDate
    query_params = {
        'attrs': 'temperature',
        'id': 'Room0,Room1',
        'aggrMethod': 'max',
        'fromDate': datetime(1970, 1, 1).isoformat(),
        'toDate': datetime(1970, 1, 6).isoformat(),
    }
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_attributes = [
        {
            'attrName': attr_name_1,
            'values': [5]
        }
    ]

    expected_entities = [
        {
            'attributes': expected_attributes,
            'entityId': 'Room0',
            'index': ['1970-01-01T00:00:00+00:00', '1970-01-06T00:00:00+00:00']
        },
        {
            'attributes': expected_attributes,
            'entityId': 'Room1',
            'index': ['1970-01-01T00:00:00+00:00', '1970-01-06T00:00:00+00:00']
        }
    ]

    expected = {
        'entities': expected_entities,
        'entityType': entity_type
    }

    obtained = r.json()
    assert isinstance(obtained, dict)
    assert obtained == expected


@pytest.mark.parametrize("aggr_period, exp_index, ins_period", [
    ("day", ['1970-01-01T00:00:00.000+00:00',
             '1970-01-02T00:00:00.000+00:00',
             '1970-01-03T00:00:00.000+00:00'], "hour"),
    ("hour", ['1970-01-01T00:00:00.000+00:00',
              '1970-01-01T01:00:00.000+00:00',
              '1970-01-01T02:00:00.000+00:00'], "minute"),
    ("minute", ['1970-01-01T00:00:00.000+00:00',
                '1970-01-01T00:01:00.000+00:00',
                '1970-01-01T00:02:00.000+00:00'], "second"),
])
@pytest.mark.parametrize("service", services)
def test_1TNENA_aggrPeriod(service, aggr_period, exp_index, ins_period):
    # Custom index to test aggrPeriod

    etype = f"test_1TNENA_aggrPeriod_{aggr_period}"
    # The reporter_dataset fixture is still in the DB cos it has a scope of
    # module. We use a different entity type to store this test's rows in a
    # different table to avoid messing up global state---see also delete down
    # below.
    eid = '{}0'.format(etype)
    for i in exp_index:
        base = dateutil.parser.isoparse(i)
        insert_test_data(service,
                         [etype],
                         index_size=5,
                         index_base=base,
                         index_period=ins_period)
    wait_for_insert([etype], service, 5 * len(exp_index))

    # aggrPeriod needs aggrMethod
    query_params = {
        'aggrPeriod': aggr_period,
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(etype=etype), params=query_params, headers=h)
    assert r.status_code == 400, r.text

    # Check aggregation with aggrPeriod
    query_params = {
        'attrs': 'temperature',
        'aggrMethod': 'sum',
        'aggrPeriod': aggr_period,
    }
    r = requests.get(query_url(etype=etype), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    exp_sum = 0 + 1 + 2 + 3 + 4

    expected_attributes = [
        {
            'attrName': attr_name_1,
            'values': [exp_sum, exp_sum, exp_sum]
        }
    ]

    expected_entities = [
        {
            'attributes': expected_attributes,
            'entityId': eid,
            'index': exp_index
        }
    ]

    expected = {
        'entities': expected_entities,
        'entityType': etype
    }

    obtained = r.json()
    assert isinstance(obtained, dict)
    assert_1TNENA_response(obtained, expected, etype=etype)
    delete_test_data(service, [etype])


@pytest.mark.parametrize("service", services)
def test_1TNENA_aggrScope(service, reporter_dataset):
    # Notify users when not yet implemented
    query_params = {
        'aggrMethod': 'avg',
        'aggrScope': 'global',
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 501, r.text
