from conftest import QL_URL
import pytest
import requests
from .utils import send_notifications, delete_entity_type, wait_for_insert

entity_type = 'TestDevice'

attr1 = 'AtTr1'
attr2 = 'aTtr_2'

attr1_value = '1'
attr2_value = 2

entity1_id = 'd1'
entity2_id = 'd2'

tenants = ['t1', 't2']


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


def insert_entities(service):
    notification_data = [{'data': mk_entities()}]
    send_notifications(service, notification_data)


@pytest.fixture(scope='module')
def manage_db_entities():
    for service in tenants:
        insert_entities(service)
    for service in tenants:
        wait_for_insert([entity_type], service, len(mk_entities()))

    yield

    for service in tenants:
        delete_entity_type(service, entity_type)


def query_sql(service, entity_id, query_params, response_code):
    url = "{}/entities/{}".format(QL_URL, entity_id)
    hs = {'Fiware-Service': service}
    response = requests.get(url, params=query_params, headers=hs)
    assert response.status_code == response_code


def query_sql_fromdate(service, entity_id, date):
    query_params = {
        'fromDate': date,
    }
    expected_response_code = 422
    query_sql(service, entity_id, query_params, expected_response_code)


def query_sql_todate(service, entity_id, date):
    query_params = {
        'toDate': date,
    }
    expected_response_code = 422
    query_sql(service, entity_id, query_params, expected_response_code)


def query_sql_limit(service, entity_id, value):
    query_params = {
        'limit': value,
    }
    expected_response_code = 400
    query_sql(service, entity_id, query_params, expected_response_code)


def query_sql_last_n(service, entity_id, value):
    query_params = {
        'lastN': value,
    }
    expected_response_code = 400
    query_sql(service, entity_id, query_params, expected_response_code)


@pytest.mark.parametrize('date', [
    "2020-03-03'%20and%20'1'%3d'1"
])
def test_sql_injection_dates(date, manage_db_entities):
    for service in tenants:
        query_sql_fromdate(service, entity1_id, date)
        query_sql_todate(service, entity1_id, date)


@pytest.mark.parametrize('value', [
    "1'%20and%20'1'%3d'1"
])
def test_sql_injection_limit_and_last(value, manage_db_entities):
    for service in tenants:
        query_sql_limit(service, entity1_id, value)
        query_sql_last_n(service, entity1_id, value)
