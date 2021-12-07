from conftest import QL_URL
from reporter.tests.utils import insert_test_data, delete_test_data, \
    wait_for_insert, wait_for_assert
import pytest
import requests
import json

entity_type = 'Room'
entity_id = 'Room0'
temperature = 'temperature'
pressure = 'pressure'
n_days = 30
services = ['t1', 't2']

query_url = "{}/op/query".format(QL_URL)


@pytest.fixture(scope='module')
def reporter_dataset():
    for service in services:
        insert_test_data(service, [entity_type], n_entities=1, index_size=30)
    for service in services:
        wait_for_insert([entity_type], service, 30)

    yield

    for service in services:
        delete_test_data(service, [entity_type])


def headers(service=None, service_path=None, content_type=True):
    h = {}
    if content_type:
        h['Content-Type'] = 'application/json'
    if service:
        h['Fiware-Service'] = service
    if service_path:
        h['Fiware-ServicePath'] = service_path

    return h


@pytest.mark.parametrize("service", services)
def test_query_defaults(service, reporter_dataset):
    body = {
        'entities': [
            {
                'type': entity_type,
                'id': entity_id
            }
        ],
        'attrs': [
            'temperature',
            'pressure'
        ]
    }

    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service))
    assert r.status_code == 200

    # Assert
    expected = [
        {
            'id': entity_id,
            'type': entity_type,
            'temperature': {
                'type': 'Number',
                'value': 29.0
            },
            'pressure': {
                'type': 'Number',
                'value': 290.0
            },
            'dateModified': {
                "type": "DateTime",
                "value": "1970-01-30T00:00:00.000+00:00"
            }
        }
    ]

    obtained = r.json()
    assert obtained == expected


@pytest.mark.parametrize("service", services)
def test_query_one_attribute(service, reporter_dataset):
    body = {
        'entities': [
            {
                'type': entity_type,
                'id': entity_id
            }
        ],
        'attrs': [
            'temperature'
        ]
    }

    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service))
    assert r.status_code == 200

    # Assert
    expected = [
        {
            'id': entity_id,
            'type': entity_type,
            'temperature': {
                'type': 'Number',
                'value': 29.0
            },
            'dateModified': {
                "type": "DateTime",
                "value": "1970-01-30T00:00:00.000+00:00"
            }
        }
    ]

    obtained = r.json()
    assert obtained == expected


@pytest.mark.parametrize("service", services)
def test_query_not_found(service, reporter_dataset):
    body = {
        'entities': [
            {
                'type': entity_type,
                'id': 'Room1'
            }
        ],
        'attrs': [
            'temperature',
            'pressure'
        ]
    }

    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service))
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


@pytest.mark.parametrize("service", services)
def test_query_expression(service, reporter_dataset):
    body = {
        'entities': [
            {
                'type': entity_type,
                'id': 'Room1'
            }
        ],
        'attrs': [
            'temperature',
            'pressure'
        ],
        'expression': {
            'q': 'temperature>20'
        }
    }

    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service))
    assert r.status_code == 400, r.text
    assert r.json() == 'expression is Not Supported'


@pytest.mark.parametrize("service", services)
def test_query_metadata(service, reporter_dataset):
    body = {
        'entities': [
            {
                'type': entity_type,
                'id': 'Room1'
            }
        ],
        'attrs': [
            'temperature',
            'pressure'
        ],
        'metadata': [
            'timestamp'
        ]
    }

    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service))
    assert r.status_code == 400, r.text
    assert r.json() == 'metadata is Not Supported'


@pytest.mark.parametrize("service", services)
def test_query_id_pattern(service, reporter_dataset):
    body = {
        'entities': [
            {
                'type': entity_type,
                'idPattern': 'True',
                'id': '.*'
            }
        ],
        'attrs': [
            'temperature',
            'pressure'
        ]
    }

    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service))
    assert r.status_code == 400, r.text
    assert r.json() == 'idPattern is Not Supported'


@pytest.mark.parametrize("service", services)
def test_query_no_type(service, reporter_dataset):
    body = {
        'entities': [
            {
                'id': 'Room0'
            }
        ],
        'attrs': [
            'temperature',
            'pressure'
        ]
    }

    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service))
    assert r.status_code == 400
    assert r.json() == 'Entity type is required'


@pytest.mark.parametrize("service", services)
def test_query_no_id(service, reporter_dataset):
    body = {
        'entities': [
            {
                'type': 'Room'
            }
        ],
        'attrs': [
            'temperature',
            'pressure'
        ]
    }

    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service))
    assert r.status_code == 400, r.text
    assert r.json() == "Entity id is required"


@pytest.mark.parametrize("service", services)
def test_default_service_path(service):
    service_path = '/'
    alt_service_path = '/notdefault'
    insert_test_data(
        service,
        [entity_type],
        n_entities=1,
        index_size=30,
        service_path=service_path)
    insert_test_data(
        service,
        [entity_type],
        n_entities=1,
        index_size=15,
        service_path=alt_service_path)

    wait_for_insert([entity_type], service, 30 + 15)

    body = {
        'entities': [
            {
                'type': entity_type,
                'id': entity_id
            }
        ],
        'attrs': [
            'temperature',
            'pressure'
        ]
    }

    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service, service_path))
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1
    assert r.json()[0]['temperature']['value'] == 29
    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service, alt_service_path))
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1
    assert r.json()[0]['temperature']['value'] == 14
    delete_test_data(service, [entity_type])


@pytest.mark.parametrize("service", services)
def test_none_service_path(service):
    service_path = None
    alt_service_path = '/notdefault'
    insert_test_data(
        service,
        [entity_type],
        n_entities=1,
        index_size=30,
        service_path=service_path)
    insert_test_data(
        service,
        [entity_type],
        n_entities=1,
        index_size=15,
        service_path=alt_service_path)

    wait_for_insert([entity_type], service, 30 + 15)

    body = {
        'entities': [
            {
                'type': entity_type,
                'id': entity_id
            }
        ],
        'attrs': [
            'temperature',
            'pressure'
        ]
    }

    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service, service_path))
    assert r.status_code == 200, r.text
    assert r.json()[0]['temperature']['value'] == 29
    assert len(r.json()) == 1
    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service, alt_service_path))
    assert r.status_code == 200, r.text
    assert r.json()[0]['temperature']['value'] == 14
    assert len(r.json()) == 1
    delete_test_data(service, [entity_type], service_path=service_path)
    delete_test_data(service, [entity_type], service_path=alt_service_path)


def test_none_service():
    service = None
    service_path = None
    alt_service_path = '/notdefault'
    insert_test_data(
        service,
        [entity_type],
        n_entities=1,
        index_size=30,
        service_path=service_path)
    insert_test_data(
        service,
        [entity_type],
        n_entities=1,
        index_size=15,
        service_path=alt_service_path)

    wait_for_insert([entity_type], service, 30 + 15)

    body = {
        'entities': [
            {
                'type': entity_type,
                'id': entity_id
            }
        ],
        'attrs': [
            'temperature',
            'pressure'
        ]
    }

    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service, service_path))
    assert r.status_code == 200, r.text
    assert r.json()[0]['temperature']['value'] == 29
    assert len(r.json()) == 1
    r = requests.post('{}'.format(query_url),
                      data=json.dumps(body),
                      headers=headers(service, alt_service_path))
    assert r.status_code == 200, r.text
    assert r.json()[0]['temperature']['value'] == 14
    assert len(r.json()) == 1
    delete_test_data(service, [entity_type], service_path=service_path)
    delete_test_data(service, [entity_type], service_path=alt_service_path)
