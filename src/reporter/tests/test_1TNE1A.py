from conftest import QL_URL
from datetime import datetime, timezone
from reporter.tests.utils import insert_test_data, delete_test_data, \
    wait_for_insert
from utils.tests.common import assert_equal_time_index_arrays
import pytest
import requests
import dateutil.parser

entity_type = 'Room'
attr_name = 'temperature'
n_days = 6
services = ['t1', 't2']
idPattern = 'R'


def query_url(values=False, etype=entity_type):
    url = "{qlUrl}/types/{entityType}/attrs/{attrName}"
    if values:
        url += '/value'
    return url.format(
        qlUrl=QL_URL,
        entityType=etype,
        attrName=attr_name,
    )


@pytest.fixture(scope='module')
def reporter_dataset():
    for service in services:
        insert_test_data(service, [entity_type], n_entities=3,
                         index_size=n_days)
    yield
    for service in services:
        delete_test_data(service, [entity_type])


def assert_1TNE1A_response(obtained, expected, etype=entity_type,
                           values_only=False):
    """
    Check API responses for 1TNE1A
    """
    assert isinstance(obtained, dict)
    if not values_only:
        assert obtained['entityType'] == etype
        assert obtained['attrName'] == attr_name
        obt_entities = obtained['entities']
        exp_entities = expected['entities']
    else:
        obt_entities = obtained['values']
        exp_entities = expected['values']

    for oe, ee in zip(obt_entities, exp_entities):
        obt_index = oe.pop('index')
        exp_index = ee.pop('index')
        assert_equal_time_index_arrays(obt_index, exp_index)

    assert obtained == expected


@pytest.mark.parametrize("service", services)
def test_1TNE1A_defaults(service, reporter_dataset):
    # Query without specific id
    query_params = {
        'type': entity_type,
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
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
    expected = {
        'entityType': entity_type,
        'attrName': attr_name,
        'entities': expected_entities
    }

    obtained = r.json()
    assert_1TNE1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1TNE1A_idPattern(service, reporter_dataset):
    query_params = {
        'idPattern': idPattern,
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
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
    expected = {
        'entityType': entity_type,
        'attrName': attr_name,
        'entities': expected_entities
    }

    obtained = r.json()
    assert_1TNE1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def idPattern_not_found(service):
    query_params = {
        'idPattern': 'nothingThere',
    }

    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


@pytest.mark.parametrize("service", services)
def test_1TNE1A_one_entity(service, reporter_dataset):
    # Query
    entity_id = 'Room1'
    query_params = {
        'type': entity_type,
        'id': entity_id
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)

    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_values,
        }
    ]
    expected = {
        'entityType': entity_type,
        'attrName': attr_name,
        'entities': expected_entities
    }
    obtained = r.json()
    assert_1TNE1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1TNE1A_some_entities(service, reporter_dataset):
    # Query
    entity_id = 'Room0,Room2'
    query_params = {
        'type': entity_type,
        'id': entity_id
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
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

    expected = {
        'entityType': entity_type,
        'attrName': attr_name,
        'entities': expected_entities
    }
    obtained = r.json()
    assert_1TNE1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_1TNE1A_values_defaults(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'id': 'Room0,,Room1,RoomNotValid',  # -> validates to Room0,Room1.
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(values=True), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
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

    obtained = r.json()
    expected = {
        'values': expected_entities
    }
    assert_1TNE1A_response(obtained, expected, values_only=True)


@pytest.mark.parametrize("service", services)
def test_not_found(service):
    query_params = {
        'type': entity_type,
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
        'type': entity_type,
        'id': 'Room1,RoomNotValid,,Room0,',  # -> validates to Room0,Room1.
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_values = list(range(n_days))
    expected_index = [
        '1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in expected_values
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

    expected = {
        'entityType': entity_type,
        'attrName': attr_name,
        'entities': expected_entities
    }
    obtained = r.json()
    assert_1TNE1A_response(obtained, expected)


@pytest.mark.parametrize("service", services)
def test_different_time_indexes(service):
    """
    Each entity should have its time_index array.
    """
    etype = 'test_different_time_indexes'
    # The reporter_dataset fixture is still in the DB cos it has a scope of
    # module. We use a different entity type to store this test's rows in a
    # different table to avoid messing up global state---see also delete down
    # below.
    insert_test_data(service, [etype], entity_id='Room1', index_size=2)
    insert_test_data(service, [etype], entity_id='Room3', index_size=4)
    insert_test_data(service, [etype], entity_id='Room2', index_size=3)

    wait_for_insert([etype], service, 2 + 4 + 3)

    query_params = {
        'type': etype,
        'id': 'Room3,Room1,Room2',
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(etype=etype), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    expected_entities = [{'entityId': 'Room3',
                          'index': ['1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in range(4)],
                          'values': list(range(4)),
                          },
                         {'entityId': 'Room1',
                          'index': ['1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in range(2)],
                          'values': list(range(2)),
                          },
                         {'entityId': 'Room2',
                          'index': ['1970-01-{:02}T00:00:00+00:00'.format(i + 1) for i in range(3)],
                          'values': list(range(3)),
                          }]

    expected = {
        'entityType': etype,
        'attrName': attr_name,
        'entities': expected_entities
    }
    obtained = r.json()
    assert_1TNE1A_response(obtained, expected, etype=etype)
    delete_test_data(service, [etype])


@pytest.mark.parametrize("service", services)
def test_aggregation_is_per_instance(service):
    """
    Attribute Aggregation works by default on a per-instance basis.
    Cross-instance aggregation not yet supported.
    It would change the shape of the response.
    """
    etype = 'test_aggregation_is_per_instance'
    # The reporter_dataset fixture is still in the DB cos it has a scope of
    # module. We use a different entity type to store this test's rows in a
    # different table to avoid messing up global state---see also delete down
    # below.
    insert_test_data(service, [etype], entity_id='Room0', index_size=3)
    insert_test_data(service, [etype], entity_id='Room1', index_size=9)

    query_params = {
        'type': etype,
        'id': 'Room0,Room1',
        'aggrMethod': 'sum'
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(etype=etype), params=query_params, headers=h)
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
    assert obtained_data['entityType'] == etype
    assert obtained_data['attrName'] == attr_name
    assert obtained_data['entities'] == expected_entities

    # Index array in the response is the used fromDate and toDate
    query_params = {
        'type': etype,
        'id': 'Room0,Room1',
        'aggrMethod': 'max',
        'fromDate': datetime(1970, 1, 1, 0, 0, 0, 0, timezone.utc).isoformat(),
        'toDate': datetime(1970, 1, 6, 0, 0, 0, 0, timezone.utc).isoformat(),
    }

    r = requests.get(query_url(etype=etype), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_entities = [{'entityId': 'Room0',
                          'index': ['1970-01-01T00:00:00+00:00',
                                      '1970-01-06T00:00:00+00:00'],
                          'values': [2],
                          },
                         {'entityId': 'Room1',
                          'index': ['1970-01-01T00:00:00+00:00',
                                    '1970-01-06T00:00:00+00:00'],
                          'values': [5],
                          }]
    obtained_data = r.json()
    assert isinstance(obtained_data, dict)
    assert obtained_data['entityType'] == etype
    assert obtained_data['attrName'] == attr_name
    assert obtained_data['entities'] == expected_entities
    delete_test_data(service, [etype])


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
def test_1TNE1A_aggrPeriod(service, aggr_period, exp_index, ins_period):
    # Custom index to test aggrPeriod
    etype = f"test_1TNE1A_aggrPeriod_{aggr_period}"
    # The reporter_dataset fixture is still in the DB cos it has a scope of
    # module. We use a different entity type to store this test's rows in a
    # different table to avoid messing up global state---see also delete down
    # below.
    eid = '{}0'.format(etype)

    for i in exp_index:
        base = dateutil.parser.isoparse(i)
        insert_test_data(service,
                         [etype],
                         entity_id=eid,
                         index_size=5,
                         index_base=base,
                         index_period=ins_period)

    wait_for_insert([etype], service, 5 * len(exp_index))

    # aggrPeriod needs aggrMethod
    query_params = {
        'type': etype,
        'aggrPeriod': aggr_period,
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(etype=etype), params=query_params, headers=h)
    assert r.status_code == 400, r.text

    # Check aggregation with aggrPeriod
    query_params = {
        'type': etype,
        'aggrMethod': 'sum',
        'aggrPeriod': aggr_period,
    }
    r = requests.get(query_url(etype=etype), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    # Assert Results
    exp_sum = 0 + 1 + 2 + 3 + 4
    expected_entities = [
        {
            'entityId': eid,
            'index': exp_index,
            'values': [exp_sum, exp_sum, exp_sum],
        }
    ]
    obtained_data = r.json()
    assert isinstance(obtained_data, dict)
    assert obtained_data['entityType'] == etype
    assert obtained_data['attrName'] == attr_name
    assert obtained_data['entities'] == expected_entities
    delete_test_data(service, [etype])


@pytest.mark.parametrize("service", services)
def test_1T1E1A_aggrScope(service, reporter_dataset):
    # Notify users when not yet implemented
    query_params = {
        'type': entity_type,
        'aggrMethod': 'avg',
        'aggrScope': 'global',
    }
    h = {'Fiware-Service': service}

    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 501, r.text
