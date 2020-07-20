from conftest import QL_URL
from datetime import datetime
from reporter.tests.utils import delete_test_data, insert_test_data
import pytest
import requests
import dateutil.parser

entity_type = "Room"
entity_type_1 = "Kitchen"
entity_id = "Room1"
entity_id_1 = "Room2"
entity_id_1_1 = 'Kitchen1'
attrs = 'pressure'
n_days = 4

default_service = 't0'
service_1 = 't1'


def query_url(values=False):
    url = "{qlUrl}/attrs"
    if values:
        url += '/value'
    return url.format(
        qlUrl=QL_URL,
    )


def query(values=False, params=None, service=default_service):
    h = {'Fiware-Service': service}
    return requests.get(query_url(values), params=params, headers=h)


@pytest.fixture(scope='module')
def reporter_dataset():

    insert_test_data(default_service, [entity_type], n_entities=1, index_size=4,
                     entity_id=entity_id)
    insert_test_data(default_service, [entity_type], n_entities=1, index_size=4,
                     entity_id=entity_id_1)

    insert_test_data(service_1, [entity_type], entity_id=entity_id,
                     index_size=3)
    insert_test_data(service_1, [entity_type_1], entity_id=entity_id_1_1,
                     index_size=3)

    yield

    delete_test_data(default_service, [entity_type])
    delete_test_data(service_1, [entity_type, entity_type_1])


def test_NTNENA_defaults(reporter_dataset):
    r = query()
    assert r.status_code == 200, r.text
    # Assert Results
    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_temperatures
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_temperatures

        }
    ]
    expected_entities_pressure = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_pressures

        }
    ]

    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_types_pressure = [
        {
            'entities': expected_entities_pressure,
            'entityType': 'Room'
        }
    ]


    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types_pressure
        },
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected


def test_NTNENA_type(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type
    }
    r = query(params=query_params)
    assert r.status_code == 200, r.text

    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    obtained = r.json()
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_values
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_temperatures

        }
    ]
    expected_entities_pressure = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_pressures

        }
    ]

    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_types_pressure = [
        {
            'entities': expected_entities_pressure,
            'entityType': 'Room'
        }
    ]
    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types_pressure
        },
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected


def test_NTNE1A_one_entity(reporter_dataset):
    # Query
    query_params = {
        'id': entity_id
    }
    r = query(params=query_params)
    assert r.status_code == 200, r.text

    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    obtained = r.json()
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_values
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        }
    ]
    expected_entities_pressure = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        }
    ]

    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_types_pressure = [
        {
            'entities': expected_entities_pressure,
            'entityType': 'Room'
        }
    ]
    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types_pressure
        },
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected


def test_1TNENA_some_entities(reporter_dataset):
    # Query
    entity_ids = 'Room1,Room2'
    query_params = {
        'id': entity_ids
    }
    r = query(params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(n_days))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_temperatures
    ]

    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_temperatures

        }
    ]
    expected_entities_pressure = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_pressures

        }
    ]

    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_types_pressure = [
        {
            'entities': expected_entities_pressure,
            'entityType': 'Room'
        }
    ]
    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types_pressure
        },
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected


def test_NTNENA_values_defaults(reporter_dataset):
    # Query
    query_params = {
        'id': 'Room1,Room2,RoomNotValid',  # -> validates to Room2,Room1.
    }
    r = query(values=True, params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(n_days))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_temperatures
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_temperatures

        }
    ]
    expected_entities_pressure = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_pressures

        }
    ]

    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_types_pressure = [
        {
            'entities': expected_entities_pressure,
            'entityType': 'Room'
        }
    ]
    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types_pressure
        },
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'values': expected_attrs
    }
    obtained = r.json()
    assert obtained == expected


def test_NTNE_fromDate_toDate(reporter_dataset):
    # Query
    query_params = {
        'fromDate': "1970-01-01T00:00:00+00:00",
        'toDate': "1970-01-04T00:00:00+00:00"
    }
    r = query(params=query_params)
    assert r.status_code == 200, r.text
    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_values
    ]
 
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_temperatures

        }
    ]
    expected_entities_pressure = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_pressures

        }
    ]

    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_types_pressure = [
        {
            'entities': expected_entities_pressure,
            'entityType': 'Room'
        }
    ]
    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types_pressure
        },
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected

def test_NTNENA_fromDate_toDate_with_quotes(reporter_dataset):
    # Query
    query_params = {
        'fromDate': '"1970-01-01T00:00:00+00:00"',
        'toDate': '"1970-01-04T00:00:00+00:00"'
    }
    r = query(params=query_params)
    assert r.status_code == 200, r.text
    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_values
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_temperatures

        }
    ]
    expected_entities_pressure = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_pressures

        }
    ]

    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_types_pressure = [
        {
            'entities': expected_entities_pressure,
            'entityType': 'Room'
        }
    ]
    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types_pressure
        },
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected

def test_NTNENA_limit(reporter_dataset):
    # Query
    query_params = {
        'limit': 10
    }
    r = query(params=query_params)
    assert r.status_code == 200, r.text

    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_values
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_temperatures

        }
    ]
    expected_entities_pressure = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_pressures

        }
    ]

    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_types_pressure = [
        {
            'entities': expected_entities_pressure,
            'entityType': 'Room'
        }
    ]
    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types_pressure
        },
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected


def test_NTNENA_combined(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'fromDate': "1970-01-01T00:00:00+00:00",
        'toDate': "1970-01-04T00:00:00+00:00",
        'limit': 10,
    }
    r = query(params=query_params)
    assert r.status_code == 200, r.text
    
    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_values
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_temperatures

        }
    ]
    expected_entities_pressure = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_pressures

        }
    ]

    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_types_pressure = [
        {
            'entities': expected_entities_pressure,
            'entityType': 'Room'
        }
    ]
    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types_pressure
        },
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected


def test_weird_ids(reporter_dataset):
    """
    Invalid ids are ignored (provided at least one is valid to avoid 404).
    Empty values are ignored.
    Order of ids is preserved in response (e.g., Room2 first, Room1 later)
    """
    query_params = {
        'id': 'Room1,RoomNotValid,Room2,',  # -> validates to Room2,Room1.
    }
    r = query(params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(n_days))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_temperatures
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_temperatures

        }
    ]
    expected_entities_pressure = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': expected_pressures

        }
    ]

    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_types_pressure = [
        {
            'entities': expected_entities_pressure,
            'entityType': 'Room'
        }
    ]
    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types_pressure
        },
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected


@pytest.mark.parametrize("aggr_period, exp_index, ins_period", [
    ("day",    ['1970-01-01T00:00:00.000+00:00',
                '1970-01-02T00:00:00.000+00:00',
                '1970-01-03T00:00:00.000+00:00'], "hour"),
    ("hour",   ['1970-01-01T00:00:00.000+00:00',
                '1970-01-01T01:00:00.000+00:00',
                '1970-01-01T02:00:00.000+00:00'], "minute"),
    ("minute", ['1970-01-01T00:00:00.000+00:00',
                '1970-01-01T00:01:00.000+00:00',
                '1970-01-01T00:02:00.000+00:00'], "second"),
])
def test_NTNENA_aggrPeriod(aggr_period, exp_index, ins_period):
    etype = 'test_NTNENA_aggrPeriod'
    # The reporter_dataset fixture is still in the DB cos it has a scope of
    # module. We use a different entity type to store this test's rows in a
    # different table to avoid messing up global state---see also delete down
    # below.
    eid = "{}0".format(etype)

    # Custom index to test aggrPeriod
    for i in exp_index:
        base = dateutil.parser.isoparse(i)
        insert_test_data(default_service,
                         [etype],
                         index_size=5,
                         index_base=base,
                         index_period=ins_period)

    # aggrPeriod needs aggrMethod
    query_params = {
        'aggrPeriod': aggr_period,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 400, r.text

    # Check aggregation with aggrPeriod
    query_params = {
        'type': etype,
        'attrs': 'temperature',
        'aggrMethod': 'sum',
        'aggrPeriod': aggr_period,
    }
    r = query(params=query_params)
    # Assert
    assert r.status_code == 200, r.text
    obtained = r.json()

    delete_test_data(default_service, [etype])

    expected_temperatures = 0 + 1 + 2 + 3 + 4
    expected_entities = [
        {
            'entityId': eid,
            'index': exp_index,
            'values': [expected_temperatures, expected_temperatures,
                       expected_temperatures]
        },
    ]
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': etype
        }
    ]
    expected_attrs = [
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'attrs': expected_attrs
    }

    assert obtained == expected


def test_not_found(reporter_dataset):
    query_params = {
        'type': 'NotThere'
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


def test_NTNENA_aggrScope(reporter_dataset):
    # Notify users when not yet implemented
    query_params = {
        'aggrMethod': 'avg',
        'aggrScope': 'global',
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 501, r.text


def test_NTNENA_types_two_attribute(reporter_dataset):
    r = query(service=service_1)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(3))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_temperatures
    ]
    expected_index_kitchen = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_temperatures
    ]
    expected_entities_kitchen = [
        {
            'entityId': entity_id_1_1,
            'index': expected_index_kitchen,
            'values': expected_pressures
        }
    ]
    expected_entities_room = [
        {
            'entityId': entity_id,
            'index': expected_index,
            'values': expected_pressures
        }
    ]
    expected_entities_kitchen_temp = [
        {
            'entityId': entity_id_1_1,
            'index': expected_index_kitchen,
            'values': expected_temperatures
        }
    ]
    expected_entities_room_temp = [
        {
            'entityId': entity_id,
            'index': expected_index,
            'values': expected_temperatures
        }
    ]
    expected_types_new = [
        {
            'entities': expected_entities_kitchen,
            'entityType': entity_type_1
        },
        {
            'entities': expected_entities_room,
            'entityType': entity_type
        }
        ]
    expected_types = [
        {
            'entities': expected_entities_kitchen_temp,
            'entityType': entity_type_1
        },
        {
            'entities': expected_entities_room_temp,
            'entityType': entity_type
        }
        ]
    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types_new
        },
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]
    expected = {
        'attrs': expected_attrs
    }
    obtained = r.json()
    assert obtained == expected


def test_1TNENA_types_one_attribute(reporter_dataset):
    query_params = {
        'attrs': 'pressure'
    }
    r = query(service=service_1, params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(3))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_temperatures
    ]
    expected_index_kitchen = [
        '1970-01-{:02}T00:00:00.000+00:00'.format(i+1) for i in expected_temperatures
    ]

    expected_entities_kitchen = [
        {
            'entityId': entity_id_1_1,
            'index': expected_index_kitchen,
            'values': expected_pressures
        }
    ]
    expected_entities_room = [
        {
            'entityId': entity_id,
            'index': expected_index,
            'values': expected_pressures
        }
    ]
    expected_types = [
        {
            'entities': expected_entities_kitchen,
            'entityType': entity_type_1
        },
        {
            'entities': expected_entities_room,
            'entityType': entity_type
        }
        ]
    expected_attrs = [
        {
            'attrName': 'pressure',
            'types': expected_types
        }
    ]
    expected = {
        'attrs': expected_attrs
    }
    obtained = r.json()
    assert obtained == expected


def test_aggregation_is_per_instance(reporter_dataset):
    query_params = {
        'attrs': 'temperature',
        'id': 'Room1,Room2',
        'aggrMethod': 'sum'
    }
    r = query(params=query_params)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_index = ['', '']
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': [sum(range(4))]
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': [sum(range(4))]

        }
    ]

    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]

    expected_attrs = [
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected
  
    # Index array in the response is the used fromDate and toDate

    query_params = {
        'attrs': 'temperature',
        'id': 'Room1',
        'aggrMethod': 'max',
        'fromDate': datetime(1970, 1, 1).isoformat(),
        'toDate': datetime(1970, 1, 2).isoformat(),
    }
    r = query(params=query_params)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_temperatures = list(range(2))
    expected_index = [
    '1970-01-{:02}T00:00:00+00:00'.format(i+1) for i in expected_temperatures
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': [1]
        }
    ]
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_attrs = [
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]
    expected = {
        'attrs': expected_attrs
    }
    obtained = r.json()
    assert obtained == expected

    query_params = {
        'attrs': 'temperature',
        'id': 'Room1',
        'aggrMethod': 'avg'
    }
    r = query(params=query_params)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_index = ['', '']
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': [sum(range(4))/4]
        }
    ]
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected_attrs = [
        {
            'attrName': 'temperature',
            'types': expected_types
        }
    ]
    expected = {
        'attrs': expected_attrs
    }
    assert obtained == expected
