from conftest import QL_URL
import pytest
import requests
from reporter.tests.utils import send_notifications, delete_entity_type, \
    wait_for_insert


entity_type = 'TestDevice'


def mk_entity(eid, coords):
    return {
        'id': eid,
        'type': entity_type,
        'location': {
            'type': 'geo:json',
            'value': {
                'type': 'LineString',
                'coordinates': coords
            }
        }
    }


entity_1 = mk_entity('d1', [[0, 0], [2, 0]])
entity_2 = mk_entity('d2', [[0, 1], [2, 1]])

services = ['t1', 't2']


@pytest.fixture(scope='module')
def setup_entities():
    notification_data = [{'data': [e]} for e in [entity_1, entity_2]]
    for service in services:
        send_notifications(service, notification_data)
        wait_for_insert([entity_type], service, 2)

    yield {}

    for service in services:
        delete_entity_type(service, entity_type)


def run_query(service, base_url, query_params, expected_status_code=200):
    h = {'Fiware-Service': service}
    r = requests.get(base_url, params=query_params, headers=h)
    assert r.status_code == expected_status_code
    return r


def query_1tne1a(service, query_params, expected_status_code=200):
    base_url = "{}/types/{}/attrs/location".format(QL_URL, entity_type)
    return run_query(service, base_url, query_params, expected_status_code)


def query_1t1ena(service, entity_id, query_params, expected_status_code=200):
    base_url = "{}/entities/{}".format(QL_URL, entity_id)
    return run_query(service, base_url, query_params, expected_status_code)


def query_1t1e1a(service, entity_id, query_params, expected_status_code=200):
    base_url = "{}/entities/{}/attrs/location".format(QL_URL, entity_id)
    return run_query(service, base_url, query_params, expected_status_code)


def eids_from_response(response):
    entities = response.json().get('entities', {})
    if not entities:
        entities = [response.json()]

    return set([e['entityId'] for e in entities])


def expected_eids(*es):
    return set([e['id'] for e in es])
