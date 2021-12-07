import requests
from conftest import QL_URL
from translators.sql_translator import entity_type
from .utils import send_notifications, delete_entity_type, wait_for_insert, \
    wait_for_assert
import pytest

services = ['t1', 't2']


def notify(service, entity):
    notification_data = [{'data': [entity]}]
    send_notifications(service, notification_data)
    wait_for_insert([entity_type(entity)], service, 1)


def get_all_stored_attributes(service, entity_id):
    h = {'Fiware-Service': service}
    url = "{}/entities/{}".format(QL_URL, entity_id)
    response = requests.get(url, headers=h)
    attrs = response.json().get('attributes', [])

    attr_values_map = {}
    for a in attrs:
        attr_values_map[a['attrName']] = a['values']  # see example below

    return attr_values_map
# e.g. curl -v http://0.0.0.0:8668/v2/entities/d:1
# returns
# {
#     "attributes": [
#       {
#         "attrName": "a1",
#         "values": [
#           123.0,
#           123.0,
#           null
#         ]
#       },
#       {
#         "attrName": "a2",
#         "values": [
#           null,
#           "new attr",
#           ""
#         ]
#       }
#     ],
#     "entityId": "d:1",
#     "index": [
#       "2018-12-20T10:50:42.438",
#       "2018-12-20T10:56:38.654",
#       "2018-12-20T11:46:21.303"
#     ]
# }


@pytest.mark.parametrize("service", services)
def test_can_add_new_attribute(service):
    a1_value = 123.0
    a2_value = 'new attribute initial value'
    entity = {
        'id': 't1:1',
        'type': 't1',
        'a1': {
            'type': 'Number',
            'value': a1_value
        }
    }
    notify(service, entity)

    entity['a2'] = {
        'type': 'Text',
        'value': a2_value
    }
    notify(service, entity)

    def add_test():
        attr_values_map = get_all_stored_attributes(service, entity['id'])
        assert len(attr_values_map) == 2
        assert attr_values_map['a1'] == [a1_value, a1_value]
        assert attr_values_map['a2'] == [None, a2_value]
    wait_for_assert(add_test)

    delete_entity_type(service, 't1')


@pytest.mark.parametrize("service", services)
def test_can_add_new_attribute_even_without_specifying_old_ones(service):
    a1_value = 123.0
    entity_1 = {
        'id': 'u1:1',
        'type': 'u1',
        'a1': {
            'type': 'Number',
            'value': a1_value
        }
    }
    notify(service, entity_1)

    a2_value = 'new attribute initial value'
    entity_2 = {
        'id': 'u1:1',
        'type': 'u1',
        'a2': {
            'type': 'Text',
            'value': a2_value
        }
    }
    notify(service, entity_2)

    def add_test():
        attr_values_map = get_all_stored_attributes(service, entity_1['id'])
        assert len(attr_values_map) == 2
        assert attr_values_map['a1'] == [a1_value, None]
        assert attr_values_map['a2'] == [None, a2_value]
    wait_for_assert(add_test)

    delete_entity_type(service, 'u1')


@pytest.mark.parametrize("service", services)
def test_can_add_2_new_attribute_even_without_specifying_old_ones(service):
    a1_value = 123.0
    entity_1 = {
        'id': 'u1:1',
        'type': 'u1',
        'a1': {
            'type': 'Number',
            'value': a1_value
        }
    }
    notify(service, entity_1)

    a2_value = 'new attribute initial value'
    a3_value = True
    entity_2 = {
        'id': 'u1:1',
        'type': 'u1',
        'a2': {
            'type': 'Text',
            'value': a2_value
        },
        'a3': {
            'type': 'Boolean',
            'value': a3_value
        }
    }
    notify(service, entity_2)

    def add_test():
        attr_values_map = get_all_stored_attributes(service, entity_1['id'])
        assert len(attr_values_map) == 3
        assert attr_values_map['a1'] == [a1_value, None]
        assert attr_values_map['a2'] == [None, a2_value]
        assert attr_values_map['a3'] == [None, a3_value]
    wait_for_assert(add_test)

    delete_entity_type(service, 'u1')


@pytest.mark.parametrize("service", services)
def test_store_missing_text_value_as_null(service):
    entity = {
        'id': 't2:1',
        'type': 't2',
        'y': {
            'type': 'Number',
            'value': '23'
        },
        'x': {
            'type': 'Text'
        }
    }
    notify(service, entity)

    attr_values_map = get_all_stored_attributes(service, entity['id'])
    assert len(attr_values_map) == 2
    assert attr_values_map['x'] == [None]
    delete_entity_type(service, 't2')


@pytest.mark.parametrize("service", services)
def test_store_missing_text_value_as_null_then_as_empty(service):
    entity = {
        'id': 't3:1',
        'type': 't3',
        'y': {
            'type': 'Number',
            'value': '23'
        },
        'x': {
            'type': 'Text'
        }
    }
    notify(service, entity)

    entity['x']['value'] = ''
    notify(service, entity)

    def add_test():
        attr_values_map = get_all_stored_attributes(service, entity['id'])
        assert len(attr_values_map) == 2
        assert attr_values_map['x'] == [None, '']
    wait_for_assert(add_test)

    delete_entity_type(service, 't3')


@pytest.mark.parametrize("service", services)
def test_store_null_text_value_as_null(service):
    entity = {
        'id': 't4:1',
        'type': 't4',
        'y': {
            'type': 'Number',
            'value': '23'
        },
        'x': {
            'type': 'Text',
            'value': None
        }
    }
    notify(service, entity)

    attr_values_map = get_all_stored_attributes(service, entity['id'])
    assert len(attr_values_map) == 2
    assert attr_values_map['x'] == [None]
    delete_entity_type(service, 't4')


@pytest.mark.parametrize("service", services)
def test_store_null_numeric_value_as_null(service):
    entity = {
        'id': 't5:1',
        'type': 't5',
        'y': {
            'type': 'Number',
            'value': '23'
        },
        'x': {
            'type': 'Number',
            'value': None
        }
    }
    notify(service, entity)

    attr_values_map = get_all_stored_attributes(service, entity['id'])
    assert len(attr_values_map) == 2
    assert attr_values_map['x'] == [None]
    delete_entity_type(service, 't5')


@pytest.mark.parametrize("service", services)
def test_store_empty_numeric_value_as_null(service):
    entity = {
        'id': 't6:1',
        'type': 't6',
        'y': {
            'type': 'Number',
            'value': '23'
        },
        'x': {
            'type': 'Number',
            'value': ''
        }
    }
    notify(service, entity)

    attr_values_map = get_all_stored_attributes(service, entity['id'])
    assert len(attr_values_map) == 2
    assert attr_values_map['x'] == [None]
    delete_entity_type(service, 't6')
