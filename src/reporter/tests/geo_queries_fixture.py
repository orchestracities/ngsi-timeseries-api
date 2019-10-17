from conftest import QL_URL
import pytest
import requests
import time
from .utils import send_notifications


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


@pytest.fixture(scope='module')
def setup_entities():
    notification_data = [{'data': [e]} for e in [entity_1, entity_2]]
    send_notifications(notification_data)

    time.sleep(2)
    yield {}

    delete_url = "{}/v2/types/{}".format(QL_URL, entity_type)
    requests.delete(delete_url)


def run_query(base_url, query_params, expected_status_code=200):
    r = requests.get(base_url, params=query_params)
    assert r.status_code == expected_status_code
    return r


def query_1tne1a(query_params, expected_status_code=200):
    base_url = "{}/v2/types/{}/attrs/location".format(QL_URL, entity_type)
    return run_query(base_url, query_params, expected_status_code)


def query_1t1ena(entity_id, query_params, expected_status_code=200):
    base_url = "{}/entities/{}".format(QL_URL, entity_id)
    return run_query(base_url, query_params, expected_status_code)


def query_1t1e1a(entity_id, query_params, expected_status_code=200):
    base_url = "{}/v2/entities/{}/attrs/location".format(QL_URL, entity_id)
    return run_query(base_url, query_params, expected_status_code)


def eids_from_response(response):
    entities = response.json().get('entities', {})
    if not entities:
        entities = [response.json()]

    return set([e['entityId'] for e in entities])


def expected_eids(*es):
    return set([e['id'] for e in es])
