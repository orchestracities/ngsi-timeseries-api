from conftest import QL_URL, do_clean_crate
import pytest
import requests
import time
import urllib
from .utils import send_notifications


entity_type = 'TestDevice'

attr1 = 'AtTr1'
attr2 = 'aTtr_2'

attr1_value = '1'
attr2_value = 2

entity1_id = 'd1'
entity2_id = 'd2'


def mk_entity(eid):
    return {
        'id': eid,
        'type': entity_type,
        attr1: {
            'type': 'Text',
            'value': attr1_value
        },
        attr2: {
            'type': 'Number',
            'value': attr2_value
        }
    }


def mk_entities():
    return [
        mk_entity(entity1_id), mk_entity(entity1_id),
        mk_entity(entity2_id), mk_entity(entity2_id)
    ]


def insert_entities():
    notification_data = [{'data': mk_entities()}]
    send_notifications(notification_data)


@pytest.fixture(scope='module')
def manage_db_entities():
    insert_entities()
    time.sleep(2)

    yield

    do_clean_crate()


def query_1t1e1a(entity_id, attr_name):
    escaped_attr_name = urllib.parse.quote(attr_name)
    url = "{}/entities/{}/attrs/{}".format(QL_URL, entity_id, escaped_attr_name)
    response = requests.get(url)
    assert response.status_code == 200
    return response.json()


def query_1tne1a(attr_name):
    escaped_attr_name = urllib.parse.quote(attr_name)
    url = "{}/types/{}/attrs/{}".format(QL_URL, entity_type, escaped_attr_name)
    response = requests.get(url)
    assert response.status_code == 200
    return response.json()


def query_1t1ena(entity_id, attr1_name, attr2_name):
    url = "{}/entities/{}".format(QL_URL, entity_id)
    query_params = {
        'attrs': attr1_name + ',' + attr2_name,
    }
    response = requests.get(url, query_params)
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize('attr_name', [
    attr1, 'attr1', 'atTr1'
])
def test_1t1e1a(attr_name, manage_db_entities):
    query_result = query_1t1e1a(entity1_id, attr_name)
    query_result.pop('index', None)
    assert query_result == {
        'attrName': attr_name,
        'entityId': entity1_id,
        'values': [attr1_value, attr1_value]
    }


@pytest.mark.parametrize('attr_name', [
    attr1, 'attr1', 'atTr1'
])
def test_1tne1a(attr_name, manage_db_entities):
    query_result = query_1tne1a(attr_name)
    for e in query_result['entities']:
        e.pop('index', None)

    assert query_result == {
        'entityType': entity_type,
        'attrName': attr_name,
        'entities': [
            {
                'entityId': entity1_id,
                'values': [attr1_value, attr1_value]
            },
            {
                'entityId': entity2_id,
                'values': [attr1_value, attr1_value]
            }
        ]
    }


@pytest.mark.parametrize('attr1_name, attr2_name', [
    (attr1, attr2), ('attr1', 'attr_2'), ('atTr1', 'ATtr_2')
])
def test_1t1ena(attr1_name, attr2_name, manage_db_entities):
    query_result = query_1t1ena(entity2_id, attr1_name, attr2_name)
    query_result.pop('index', None)

    assert query_result == {
        'entityId': entity2_id,
        'attributes': [
            {
                'attrName': attr1,
                'values': [attr1_value, attr1_value]
            },
            {
                'attrName': attr2,
                'values': [attr2_value, attr2_value]
            }
        ]
    }
