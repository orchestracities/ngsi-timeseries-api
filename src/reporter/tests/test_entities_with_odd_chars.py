from conftest import QL_URL
import pytest
import requests
import urllib
from reporter.tests.utils import send_notifications, delete_entity_type, \
    wait_for_insert

SLEEP_TIME = 1


def mk_entity(eid, entity_type, attr_name):
    return {
        'id': eid,
        'type': entity_type,
        attr_name: {
            'type': 'Text',
            'value': 'test'
        }
    }


def insert_entity(service, entity):
    notification_data = [{'data': [entity]}]
    send_notifications(service, notification_data)


def query_entity(service, entity_id, attr_name):
    escaped_attr_name = urllib.parse.quote(attr_name)
    url = "{}/entities/{}/attrs/{}".format(QL_URL,
                                           entity_id, escaped_attr_name)
    h = {'Fiware-Service': service}
    response = requests.get(url, headers=h)
    assert response.status_code == 200
    return response.json()


def run_test(service, entity_type, attr_name):
    entity = mk_entity('d1', entity_type, attr_name)

    insert_entity(service, entity)
    wait_for_insert([entity_type], service, 1)

    query_result = query_entity(service, entity['id'], attr_name)
    query_result.pop('index', None)
    assert query_result == {
        'attrName': attr_name,
        'entityId': entity['id'],
        'entityType': entity_type,
        'values': [entity[attr_name]['value']]
    }

    delete_entity_type(service, entity_type)


odd_chars = ['-', '+', '@', ':']
# Note that you can't use certain chars at all, even if quoted. Three
# such chars are '.', '#' and  ' '. So for example, CrateDB bombs out
# on `create table "x.y" (...)` or `create table "x y" (...)`


@pytest.mark.parametrize('char', odd_chars)
@pytest.mark.parametrize("service", [
    "t1", "t2"
])
def test_odd_char_in_entity_type(service, char):
    entity_type = 'test{}device'.format(char)
    attr_name = 'plain_name'
    run_test(service, entity_type, attr_name)


@pytest.mark.parametrize('char', odd_chars)
@pytest.mark.parametrize("service", [
    "t1", "t2"
])
def test_odd_char_in_attr_name(service, char):
    entity_type = 'test_device'
    attr_name = 'weird{}name'.format(char)
    run_test(service, entity_type, attr_name)


@pytest.mark.parametrize('char', odd_chars)
@pytest.mark.parametrize("service", [
    "t1", "t2"
])
def test_odd_char_in_entity_type_and_attr_name(service, char):
    entity_type = 'test{}device'.format(char)
    attr_name = 'weird{}name'.format(char)
    run_test(service, entity_type, attr_name)
