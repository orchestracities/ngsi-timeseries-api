from conftest import QL_URL, crate_translator as translator
from datetime import datetime
from reporter.tests.utils import insert_test_data
from utils.common import assert_equal_time_index_arrays
import pytest
import requests


entity_type = "Room"
entity_type_1 = "Kitchen"
entity_id = "Room1"
entity_id_1 = "Room2"
attrs = 'pressure'
n_days = 4

def query_url(values=False):
    url = "{qlUrl}/attrs"
    if values:
        url += '/value'
    return url.format(
        qlUrl=QL_URL,
    )

@pytest.fixture()
def reporter_dataset(translator):
    insert_test_data(translator, [entity_type], n_entities=1, index_size=4, entity_id=entity_id)
    insert_test_data(translator, [entity_type], n_entities=1, index_size=4, entity_id=entity_id_1)
    #insert_test_data(translator, [entity_type_1], n_entities=1, index_size=4, entity_id=entity_id)
    #insert_test_data(translator, [entity_type_1], n_entities=1, index_size=4, entity_id=entity_id_1) 
    yield

def test_NTNENA_defaults(reporter_dataset):
    r = requests.get(query_url())
    assert r.status_code == 200, r.text
    # Assert Results
    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_temperatures
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
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text
    
    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    obtained = r.json()
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_values
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
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    obtained = r.json()
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_values
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
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(n_days))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_temperatures
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
    r = requests.get(query_url(values=True), params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(n_days))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_temperatures
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
        'fromDate': "1970-01-01T00:00:00",
        'toDate': "1970-01-04T00:00:00"
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text
    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    obtained = r.json()
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_values
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
        'fromDate': '"1970-01-01T00:00:00"',
        'toDate': '"1970-01-04T00:00:00"'
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text
    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    obtained = r.json()
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_values
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
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    obtained = r.json()
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_values
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
        'fromDate': "1970-01-01T00:00:00",
        'toDate': "1970-01-04T00:00:00",
        'limit': 10,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text
    
    expected_temperatures = list(range(4))
    expected_pressures = [t*10 for t in expected_temperatures]
    # Assert
    obtained = r.json()
    expected_values = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_values
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
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(n_days))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_temperatures
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
    ("day",    ['1970-01-01T00:00:00.000',
                '1970-01-02T00:00:00.000',
                '1970-01-03T00:00:00.000'], "hour"),
    ("hour",   ['1970-01-01T00:00:00.000',
                '1970-01-01T01:00:00.000',
                '1970-01-01T02:00:00.000'], "minute"),
    ("minute", ['1970-01-01T00:00:00.000',
                '1970-01-01T00:01:00.000',
                '1970-01-01T00:02:00.000'], "second"),
])
def test_NTNENA_aggrPeriod(translator, aggr_period, exp_index, ins_period):
    # Custom index to test aggrPeriod
    for i in exp_index:
        base = datetime.strptime(i, "%Y-%m-%dT%H:%M:%S.%f")
        insert_test_data(translator,
                         [entity_type],
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
        'attrs': 'temperature',
        'aggrMethod': 'sum',
        'aggrPeriod': aggr_period,
    }
    r = requests.get(query_url(), params=query_params)
    # Assert
    assert r.status_code == 200, r.text
    expected_temperatures = 0 + 1 + 2 + 3 + 4
    obtained = r.json()
    expected_entities = [
        {
            'entityId': 'Room0',
            'index': exp_index,
            'values': [expected_temperatures, expected_temperatures, expected_temperatures]
        },
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

def test_not_found():
    r = requests.get(query_url())
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

def test_NTNENA_types_two_attribute(translator):
    # Query
    t = 'Room'
    t1 = 'Kitchen'

    insert_test_data(translator,[t], entity_id='Room1', index_size=3)
    insert_test_data(translator,[t1], entity_id='Kitchen1', index_size=3)

    r = requests.get(query_url())
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(3))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_temperatures
    ]
    expected_index_kitchen = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_temperatures
    ]
    expected_entities_kitchen = [
        {
            'entityId': 'Kitchen1',
            'index': expected_index_kitchen,
            'values': expected_pressures
        }
    ]
    expected_entities_room = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        }
    ]
    expected_entities_kitchen_temp = [
        {
            'entityId': 'Kitchen1',
            'index': expected_index_kitchen,
            'values': expected_temperatures
        }
    ]
    expected_entities_room_temp = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        }
    ]
    expected_types_new = [
        {
            'entities': expected_entities_kitchen,
            'entityType': 'Kitchen'
        },
        {
            'entities': expected_entities_room,
            'entityType': 'Room'
        }
        ]
    expected_types = [
        {   'entities': expected_entities_kitchen_temp,
            'entityType': 'Kitchen'
        },
        {
            'entities': expected_entities_room_temp,
            'entityType': 'Room'
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


def test_1TNENA_types_one_attribute(translator):
    # Query
    t = 'Room'
    t1 = 'Kitchen'

    insert_test_data(translator,[t], entity_id='Room1', index_size=3)
    insert_test_data(translator,[t1], entity_id='Kitchen1', index_size=3)

    query_params = {
        'attrs': 'pressure'
    }
    r = requests.get(query_url(),params=query_params)
    assert r.status_code == 200, r.text

    # Assert Results
    expected_temperatures = list(range(3))
    expected_pressures = [t*10 for t in expected_temperatures]
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_temperatures
    ]
    expected_index_kitchen = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_temperatures
    ]

    expected_entities_kitchen = [
        {
            'entityId': 'Kitchen1',
            'index': expected_index_kitchen,
            'values': expected_pressures
        }
    ]
    expected_entities_room = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_pressures
        }
    ]
    expected_types = [
        {
            'entities': expected_entities_kitchen,
            'entityType': 'Kitchen'
        },
        {
            'entities': expected_entities_room,
            'entityType': 'Room'
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

def test_aggregation_is_per_instance(translator):
    
    t = 'Room'
    insert_test_data(translator, [t], entity_id='Room1', index_size=3)
    insert_test_data(translator, [t], entity_id='Room2', index_size=3)

    query_params = {
        'attrs': 'temperature',
        'id': 'Room1,Room2',
        'aggrMethod': 'sum'
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_temperatures = list(range(4))
    expected_index = [
        '',''
    ]
    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': [sum(range(3))]
        },
        {
            'entityId': 'Room2',
            'index': expected_index,
            'values': [sum(range(3))]

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
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_temperatures = list(range(2))
    expected_index = [
    '1970-01-{:02}T00:00:00'.format(i+1) for i in expected_temperatures
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
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_temperatures = list(range(4))
    expected_index = [
        '',''
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
    assert obtained == expected
