from conftest import QL_URL
from reporter.tests.utils import delete_test_data, \
    insert_test_data_different_types, wait_for_insert
import pytest
import requests

entity_type = "TestRoomAggregationDifferentTypes"
entity_id = "TestRoomAggregationDifferentTypes1"
n_days = 4

services = ['t1', 't2']


def query_url(url_path):
    url = "{qlUrl}/{url_path}"
    return url.format(
        qlUrl=QL_URL,
        url_path=url_path
    )


def query(url_path, params=None, service=None):
    h = {'Fiware-Service': service}
    return requests.get(query_url(url_path), params=params, headers=h)


@pytest.fixture(scope='module')
def reporter_dataset_different_attribute_types():
    for service in services:
        insert_test_data_different_types(
            service,
            [entity_type],
            n_entities=1,
            index_size=4,
            entity_id=entity_id)
        wait_for_insert([entity_type], service, 4)

    yield
    for service in services:
        delete_test_data(service, [entity_type])


def test_aggregation_on_different_attribute_types_timescale(
        reporter_dataset_different_attribute_types, service='t2'):
    attrs = 'temperature,intensity,boolean'
    query_params = {
        'attrs': attrs,
        'aggrMethod': 'min'
    }
    # timescale do not support min on boolean
    # /attrs
    r = query(url_path="attrs", params=query_params, service=service)
    assert r.status_code == 404, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected = 'AggrMethod cannot be applied'

    assert obtained['error'] == expected

    # /entities/{eid}
    r = query(
        url_path="entities/TestRoomAggregationDifferentTypes1",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected = 'AggrMethod cannot be applied'

    assert obtained['error'] == expected

    # /types/{etype}
    r = query(
        url_path="types/TestRoomAggregationDifferentTypes",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected = 'AggrMethod cannot be applied'

    assert obtained['error'] == expected

    # 'aggrMethod': 'max'
    # /attrs

    query_params = {
        'attrs': attrs,
        'aggrMethod': 'max',
    }

    # timescale do not support max on boolean
    r = query(url_path="attrs", params=query_params, service=service)
    assert r.status_code == 404, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected = 'AggrMethod cannot be applied'

    assert obtained['error'] == expected

    # /entities/{eid}
    r = query(
        url_path="entities/TestRoomAggregationDifferentTypes1",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected = 'AggrMethod cannot be applied'

    assert obtained['error'] == expected

    # /types/{etype}
    r = query(
        url_path="types/TestRoomAggregationDifferentTypes",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected = 'AggrMethod cannot be applied'

    assert obtained['error'] == expected

    # 'aggrMethod': 'count'
    # /attrs

    query_params = {
        'attrs': attrs,
        'aggrMethod': 'count',
    }
    r = query(url_path="attrs", params=query_params, service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_attrs = [
        {
            'attrName': 'boolean',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': [4]
                }],
                'entityType': entity_type
            }]
        },
        {
            'attrName': 'intensity',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': [4]
                }],
                'entityType': entity_type
            }]
        },
        {
            'attrName': 'temperature',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': [4]
                }],
                'entityType': entity_type
            }]
        },
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected

    # /entities/{eid}
    r = query(
        url_path="entities/TestRoomAggregationDifferentTypes1",
        params=query_params,
        service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_attrs = [
        {
            'attrName': 'boolean',
            'values': [4]
        },
        {
            'attrName': 'intensity',
            'values': [4]
        },
        {
            'attrName': 'temperature',
            'values': [4]
        }
    ]

    expected = {
        'index': [],
        'attributes': expected_attrs,
        'entityId': entity_id,
        'entityType': entity_type
    }
    obtained = r.json()
    assert obtained == expected

    # /types/{etype}
    r = query(
        url_path="types/TestRoomAggregationDifferentTypes",
        params=query_params,
        service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_values = [
        {
            'attributes': [
                {
                    'attrName': 'boolean',
                    'values': [4]
                },
                {
                    'attrName': 'intensity',
                    'values': [4]
                },
                {
                    'attrName': 'temperature',
                    'values': [4]
                }
            ],
            'entityId': entity_id,
            'index': ['', '']
        }
    ]

    expected = {
        'entities': expected_values,
        'entityType': entity_type
    }

    obtained = r.json()
    assert obtained == expected

    # 'aggrMethod': 'avg'
    # /attrs
    query_params = {
        'attrs': attrs,
        'aggrMethod': 'avg'
    }
    r = query(url_path="attrs", params=query_params, service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }

    # /entities/{eid}
    r = query(
        url_path="entities/TestRoomAggregationDifferentTypes1",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }

    # /types/{etype}
    r = query(
        url_path="types/TestRoomAggregationDifferentTypes",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }

    # 'aggrMethod': 'sum'
    # /attrs
    query_params = {
        'attrs': attrs,
        'aggrMethod': 'sum'
    }
    r = query(url_path="attrs", params=query_params, service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }

    # /entities/{eid}
    r = query(
        url_path="entities/TestRoomAggregationDifferentTypes1",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }

    # /types/{etype}
    r = query(
        url_path="types/TestRoomAggregationDifferentTypes",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }


def test_aggregation_on_different_data_types_crate(
        reporter_dataset_different_attribute_types, service='t1'):
    attrs = 'temperature,intensity,boolean'
    query_params = {
        'attrs': attrs,
        'aggrMethod': 'min',
        'type': entity_type
    }
    # crate supports min on boolean
    # /attrs
    r = query(url_path="attrs", params=query_params, service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected_attrs = [
        {
            'attrName': 'boolean',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': [False]
                }],
                'entityType': entity_type
            }]
        },
        {
            'attrName': 'intensity',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': ['str1']
                }],
                'entityType': entity_type
            }]
        },
        {
            'attrName': 'temperature',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': [0.0]
                }],
                'entityType': entity_type
            }]
        },
    ]

    expected = {
        'attrs': expected_attrs
    }
    assert obtained == expected

    # /entities/{eid}
    r = query(
        url_path="entities/TestRoomAggregationDifferentTypes1",
        params=query_params,
        service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected_attrs = [
        {
            'attrName': 'boolean',
            'values': [False]
        },
        {
            'attrName': 'intensity',
            'values': ['str1']
        },
        {
            'attrName': 'temperature',
            'values': [0.0]
        }
    ]

    expected = {
        'index': [],
        'attributes': expected_attrs,
        'entityId': entity_id,
        'entityType': entity_type
    }

    assert obtained == expected

    # /types/{etype}
    r = query(
        url_path="types/TestRoomAggregationDifferentTypes",
        params=query_params,
        service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_values = [
        {
            'attributes': [
                {
                    'attrName': 'boolean',
                    'values': [False]
                },
                {
                    'attrName': 'intensity',
                    'values': ['str1']
                },
                {
                    'attrName': 'temperature',
                    'values': [0.0]
                }
            ],
            'entityId': entity_id,
            'index': ['', '']
        }
    ]

    expected = {
        'entities': expected_values,
        'entityType': entity_type
    }

    assert obtained == expected

    # 'aggrMethod': 'max'
    # /attrs

    query_params = {
        'attrs': attrs,
        'aggrMethod': 'max',
    }
    r = query(url_path="attrs", params=query_params, service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_attrs = [
        {
            'attrName': 'boolean',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': [True]
                }],
                'entityType': entity_type
            }]
        },
        {
            'attrName': 'intensity',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': ['str1']
                }],
                'entityType': entity_type
            }]
        },
        {
            'attrName': 'temperature',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': [3.0]
                }],
                'entityType': entity_type
            }]
        },
    ]

    expected = {
        'attrs': expected_attrs
    }
    obtained = r.json()
    assert obtained == expected

    # /entities/{eid}
    r = query(
        url_path="entities/TestRoomAggregationDifferentTypes1",
        params=query_params,
        service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected_attrs = [
        {
            'attrName': 'boolean',
            'values': [True]
        },
        {
            'attrName': 'intensity',
            'values': ['str1']
        },
        {
            'attrName': 'temperature',
            'values': [3.0]
        }
    ]

    expected = {
        'index': [],
        'attributes': expected_attrs,
        'entityId': entity_id,
        'entityType': entity_type
    }

    obtained = r.json()
    assert obtained == expected

    # /types/{etype}
    r = query(
        url_path="types/TestRoomAggregationDifferentTypes",
        params=query_params,
        service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected_values = [
        {
            'attributes': [
                {
                    'attrName': 'boolean',
                    'values': [True]
                },
                {
                    'attrName': 'intensity',
                    'values': ['str1']
                },
                {
                    'attrName': 'temperature',
                    'values': [3.0]
                }
            ],
            'entityId': entity_id,
            'index': ['', '']
        }
    ]

    expected = {
        'entities': expected_values,
        'entityType': entity_type
    }

    obtained = r.json()
    assert obtained == expected

    # 'aggrMethod': 'count'
    # /attrs

    query_params = {
        'attrs': attrs,
        'aggrMethod': 'count',
    }
    r = query(url_path="attrs", params=query_params, service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)
    expected_attrs = [
        {
            'attrName': 'boolean',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': [4]
                }],
                'entityType': entity_type
            }]
        },
        {
            'attrName': 'intensity',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': [4]
                }],
                'entityType': entity_type
            }]
        },
        {
            'attrName': 'temperature',
            'types':
            [{
                'entities':
                [{
                    'entityId': entity_id,
                    'index': ['', ''],
                    'values': [4]
                }],
                'entityType': entity_type
            }]
        },
    ]

    expected = {
        'attrs': expected_attrs
    }

    obtained = r.json()
    assert obtained == expected

    # /entities/{eid}
    r = query(
        url_path="entities/TestRoomAggregationDifferentTypes1",
        params=query_params,
        service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected_attrs = [
        {
            'attrName': 'boolean',
            'values': [4]
        },
        {
            'attrName': 'intensity',
            'values': [4]
        },
        {
            'attrName': 'temperature',
            'values': [4]
        }
    ]

    expected = {
        'index': [],
        'attributes': expected_attrs,
        'entityId': entity_id,
        'entityType': entity_type
    }

    obtained = r.json()
    assert obtained == expected

    # /types/{etype}
    r = query(
        url_path="types/TestRoomAggregationDifferentTypes",
        params=query_params,
        service=service)
    assert r.status_code == 200, r.text

    obtained = r.json()
    assert isinstance(obtained, dict)

    expected_values = [
        {
            'attributes': [
                {
                    'attrName': 'boolean',
                    'values': [4]
                },
                {
                    'attrName': 'intensity',
                    'values': [4]
                },
                {
                    'attrName': 'temperature',
                    'values': [4]
                }
            ],
            'entityId': entity_id,
            'index': ['', '']
        }
    ]

    expected = {
        'entities': expected_values,
        'entityType': entity_type
    }

    obtained = r.json()
    assert obtained == expected

    # 'aggrMethod': 'avg'
    # /attrs

    query_params = {
        'attrs': attrs,
        'aggrMethod': 'avg'
    }
    r = query(url_path="attrs", params=query_params, service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }

    # /entities/{eid}
    r = query(
        url_path="entities/TestRoomAggregationDifferentTypes1",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }

    # /types/{etype}
    r = query(
        url_path="types/TestRoomAggregationDifferentTypes",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }

    # 'aggrMethod': 'sum'
    # attrs

    query_params = {
        'attrs': attrs,
        'aggrMethod': 'sum'
    }
    r = query(url_path="attrs", params=query_params, service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }

    # /entities/{eid}
    r = query(
        url_path="entities/TestRoomAggregationDifferentTypes1",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }

    # /types/{etype}
    r = query(
        url_path="types/TestRoomAggregationDifferentTypes",
        params=query_params,
        service=service)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "AggrMethod cannot be applied",
        "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."
    }
