from conftest import QL_URL
import pytest
import requests
import time
import urllib
from .utils import send_notifications


def mk_entity(eid, entity_type, attr_name):
    return {
        'id': eid,
        'type': entity_type,
        attr_name: {
            'type': 'Text',
            'value': 'test'
        }
    }


def insert_entity(entity):
    notification_data = [{'data': [entity]}]
    send_notifications(notification_data)

    time.sleep(2)


def query_entity(entity_id, attr_name):
    escaped_attr_name = urllib.parse.quote(attr_name)
    url = "{}/entities/{}/attrs/{}".format(QL_URL, entity_id, escaped_attr_name)
    response = requests.get(url)
    assert response.status_code == 200
    return response.json().get('data', {})


def delete_entities(entity_type):
    delete_url = "{}/types/{}".format(QL_URL, entity_type)
    response = requests.delete(delete_url)
    assert response.ok


def run_test(entity_type, attr_name):
    entity = mk_entity('d1', entity_type, attr_name)

    insert_entity(entity)

    query_result = query_entity(entity['id'], attr_name)
    query_result.pop('index', None)
    assert query_result == {
        'attrName': attr_name,
        'entityId': entity['id'],
        'values': [entity[attr_name]['value']]
    }

    delete_entities(entity['type'])


odd_chars = ['-', '+', '@', ':']
# Note that you can't use certain chars at all, even if quoted. Three
# such chars are '.', '#' and  ' '. So for example, CrateDB bombs out
# on `create table "x.y" (...)` or `create table "x y" (...)`


@pytest.mark.parametrize('char', odd_chars)
def test_odd_char_in_entity_type(char, clean_mongo, clean_crate):
    entity_type = 'test{}device'.format(char)
    attr_name = 'plain_name'
    run_test(entity_type, attr_name)


@pytest.mark.parametrize('char', odd_chars)
def test_odd_char_in_attr_name(char, clean_mongo, clean_crate):
    entity_type = 'test_device'
    attr_name = 'weird{}name'.format(char)
    run_test(entity_type, attr_name)


@pytest.mark.parametrize('char', odd_chars)
def test_odd_char_in_entity_type_and_attr_name(char, clean_mongo, clean_crate):
    entity_type = 'test{}device'.format(char)
    attr_name = 'weird{}name'.format(char)
    run_test(entity_type, attr_name)
