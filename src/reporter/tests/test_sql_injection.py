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
        mk_entity(entity2_id), mk_entity(entity2_id),
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


def query_sql_fromdate(entity_id, date):
    url = "{}/entities/{}".format(QL_URL, entity_id)
    query_params = {
        'fromDate': date,
    }
    response = requests.get(url, query_params)
    assert response.status_code == 422

def query_sql_todate(entity_id, date):
    url = "{}/entities/{}".format(QL_URL, entity_id)
    query_params = {
        'toDate': date,
    }
    response = requests.get(url, query_params)
    assert response.status_code == 422

def query_sql_limit(entity_id, value):
    url = "{}/entities/{}".format(QL_URL, entity_id)
    query_params = {
        'limit': value,
    }
    response = requests.get(url, query_params)
    assert response.status_code == 400

def query_sql_last_n(entity_id, value):
    url = "{}/entities/{}".format(QL_URL, entity_id)
    query_params = {
        'lastN': value,
    }
    response = requests.get(url, query_params)
    assert response.status_code == 400

@pytest.mark.parametrize('date', [
    "2020-03-03'%20and%20'1'%3d'1"
])
def test_sql_injection_dates(date, manage_db_entities):
    query_sql_fromdate(entity1_id, date)
    query_sql_todate(entity1_id, date)

@pytest.mark.parametrize('value', [
    "1'%20and%20'1'%3d'1"
])
def test_sql_injection_limit_and_last(value, manage_db_entities):
    query_sql_limit(entity1_id, value)
    query_sql_last_n(entity1_id, value)
