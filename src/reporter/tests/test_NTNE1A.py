from conftest import QL_URL, crate_translator as translator
from reporter.tests.utils import insert_test_data
from datetime import datetime
import pytest
import requests

attr_name = 'temperature'
entity_type = "Room"
entity_id = "Room1"
entity_id_1 = "Room2"
n_days = 4

def query_url(values=False):
    url = "{qlUrl}/attrs/{attrName}"
    if values:
        url += '/value'
    return url.format(
        qlUrl=QL_URL,
        attrName=attr_name
    )

@pytest.fixture()
def reporter_dataset(translator):
    insert_test_data(translator, [entity_type], n_entities=1, index_size=4, entity_id=entity_id)
    insert_test_data(translator, [entity_type], n_entities=1, index_size=4, entity_id=entity_id_1)
    yield

def test_NTNE1A_defaults(reporter_dataset):
    r = requests.get(query_url())
    # Assert Results
    assert r.status_code == 200, r.text

    expected_temperatures = list(range(4))
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
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types
    }
    obtained = r.json()
    assert obtained == expected


def test_NTNE1A_type(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text
    expected_temperatures = list(range(4))
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
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types
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

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)

    expected_temperatures = list(range(4))
    expected_index = [
        '1970-01-{:02}T00:00:00.000'.format(i+1) for i in expected_temperatures
    ]

    expected_entities = [
        {
            'entityId': 'Room1',
            'index': expected_index,
            'values': expected_temperatures
        }
    ]
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types
    }
    obtained = r.json()
    assert obtained == expected


def test_1TNENA_some_entities(reporter_dataset):
    # Query
    # Assert Results
    entity_ids = "Room1, Room2"
    query_params = {
        'id': entity_ids
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    obtained_data = r.json()
    assert isinstance(obtained_data, dict)
    expected_temperatures = list(range(4))
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
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types
    }
    obtained = r.json()
    assert obtained == expected


def test_NTNE1A_values_defaults(reporter_dataset):
    # Query
    query_params = {
        'id': 'Room1,Room2,RoomNotValid',  # -> validates to Room1,Room2.
    } 
    r = requests.get(query_url(values=True), params=query_params)
    assert r.status_code == 200, r.text
    
    # Assert Results
    expected_temperatures = list(range(4))
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
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        #'values': expected_entities,
        #'attrName': attr_name,
        'values': expected_types
        #'types': expected_types
    }

    obtained = r.json()
    assert obtained == expected


def test_weird_ids(reporter_dataset):
    """
    Invalid ids are ignored (provided at least one is valid to avoid 404).
    Empty values are ignored.
    Order of ids is preserved in response (e.g., Room1 first, Room0 later)
    """
    query_params = {
        'id': 'Room1,RoomNotValid,Room2,',  # -> validates to Room2,Room1.
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text
    expected_temperatures = list(range(n_days))
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
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types
    }
    obtained = r.json()
    assert obtained == expected


def test_NTNE1A_fromDate_toDate(reporter_dataset):
    # Query
    query_params = {
        'types': 'entity_type',
        'fromDate': "1970-01-01T00:00:00",
        'toDate': "1970-01-04T00:00:00"
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_temperatures = list(range(4))
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
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types,
    }
   
    obtained = r.json()
    assert obtained == expected


def test_NTNE1A_fromDate_toDate_with_quotes(reporter_dataset):
    # Query
    query_params = {
        'types': 'entity_type',   
        'fromDate': "1970-01-01T00:00:00",
        'toDate': "1970-01-04T00:00:00"
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text
    
    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_temperatures = list(range(4))
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
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types,
    }
    obtained = r.json()
    assert obtained == expected


def test_NTNE1A_limit(reporter_dataset):
    # Query
    query_params = {
        'limit': 10
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_temperatures = list(range(4))
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
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types,
    }
    obtained = r.json()
    assert obtained == expected


def test_NTNE1A_combined(reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'fromDate': "1970-01-01T00:00:00",
        'toDate': "1970-01-03T00:00:00",
        'limit': 10,
    }
    
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_temperatures = list(range(3))
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
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types,
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
def test_NTNE1A_aggrPeriod(translator, aggr_period, exp_index, ins_period):
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
    assert r.status_code == 200, r.text
    expected_temperatures = 0 + 1 + 2 + 3 + 4
    # Assert
    obtained = r.json()
    expected_entities = [
        {
            'entityId': 'Room0',
            'index': exp_index,
            'values': [expected_temperatures, expected_temperatures, expected_temperatures]
        } 
    ]
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types,
    }
    obtained = r.json()
    assert obtained == expected


def test_not_found():
    query_params = {
        'id': 'RoomNotValid'
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


def test_NTNE1A_aggrScope(reporter_dataset):
    # Notify users when not yet implemented
    query_params = {
        'aggrMethod': 'avg',
        'aggrScope': 'global',
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 501, r.text


def test_aggregation_is_per_instance(translator):
    t = 'Room'
    insert_test_data(translator, [t], entity_id='Room1', index_size=3)

    query_params = {
        'attrs': 'temperature',
        'id': 'Room1',
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
        }
    ]
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': 'Room'
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types,
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
    expected = {
        'attrName': attr_name,
        'types': expected_types,
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
    expected = {
        'attrName': attr_name,
        'types': expected_types,
    }
    obtained = r.json()
    assert obtained == expected
