from conftest import QL_URL
import pytest
import requests
import time
import urllib
from .utils import send_notifications


attr1 = 'AtTr1'
attr2 = 'aTtr_2'


def mk_entity(eid):
    return {
        'id': eid,
        'type': 'TestDevice',
        attr1: {
            'type': 'Text',
            'value': '1'
        },
        attr2: {
            'type': 'Number',
            'value': 2
        }
    }


def insert_entities(entities):
    notification_data = [{'data': entities}]
    send_notifications(notification_data)

    time.sleep(2)


def query_1t1e1a(entity_id, attr_name):
    escaped_attr_name = urllib.parse.quote(attr_name)
    url = "{}/entities/{}/attrs/{}".format(QL_URL, entity_id, escaped_attr_name)
    response = requests.get(url)
    assert response.status_code == 200
    return response.json().get('data', {})


@pytest.mark.parametrize('attr_name', [
    attr1, 'attr1', 'atTr1'
])
def test_1t1e1a(attr_name, clean_crate):
    entity = mk_entity('d1')

    insert_entities([entity])

    query_result = query_1t1e1a(entity['id'], attr_name)
    query_result.pop('index', None)
    assert query_result == {
        'attrName': attr_name,
        'entityId': entity['id'],
        'values': [entity[attr1]['value']]
    }


