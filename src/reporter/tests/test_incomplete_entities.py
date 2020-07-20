import requests
import time
from conftest import QL_URL
from .utils import send_notifications


def notify(entity):
    service = ''
    notification_data = [{'data': [entity]}]
    send_notifications(service, notification_data)


def get_all_stored_attributes(entity_id):
    time.sleep(2)

    url = "{}/entities/{}".format(QL_URL, entity_id)
    response = requests.get(url)
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


def test_can_add_new_attribute():
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
    notify(entity)

    entity['a2'] = {
        'type': 'Text',
        'value': a2_value
    }
    notify(entity)

    attr_values_map = get_all_stored_attributes(entity['id'])
    assert len(attr_values_map) == 2
    assert attr_values_map['a1'] == [a1_value, a1_value]
    assert attr_values_map['a2'] == [None, a2_value]


def test_can_add_new_attribute_even_without_specifying_old_ones():
    a1_value = 123.0
    entity_1 = {
        'id': 'u1:1',
        'type': 'u1',
        'a1': {
            'type': 'Number',
            'value': a1_value
        }
    }
    notify(entity_1)

    a2_value = 'new attribute initial value'
    entity_2 = {
        'id': 'u1:1',
        'type': 'u1',
        'a2': {
            'type': 'Text',
            'value': a2_value
        }
    }
    notify(entity_2)

    attr_values_map = get_all_stored_attributes(entity_1['id'])
    assert len(attr_values_map) == 2
    assert attr_values_map['a1'] == [a1_value, None]
    assert attr_values_map['a2'] == [None, a2_value]


def test_store_missing_text_value_as_null():
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
    notify(entity)

    attr_values_map = get_all_stored_attributes(entity['id'])
    assert len(attr_values_map) == 2
    assert attr_values_map['x'] == [None]


def test_store_missing_text_value_as_null_then_as_empty():
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
    notify(entity)

    entity['x']['value'] = ''
    notify(entity)

    attr_values_map = get_all_stored_attributes(entity['id'])
    assert len(attr_values_map) == 2
    assert attr_values_map['x'] == [None, '']


def test_store_null_text_value_as_null():
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
    notify(entity)

    attr_values_map = get_all_stored_attributes(entity['id'])
    assert len(attr_values_map) == 2
    assert attr_values_map['x'] == [None]


def test_store_null_numeric_value_as_null():
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
    notify(entity)

    attr_values_map = get_all_stored_attributes(entity['id'])
    assert len(attr_values_map) == 2
    assert attr_values_map['x'] == [None]


def test_store_empty_numeric_value_as_null():
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
    notify(entity)

    attr_values_map = get_all_stored_attributes(entity['id'])
    assert len(attr_values_map) == 2
    assert attr_values_map['x'] == [None]


