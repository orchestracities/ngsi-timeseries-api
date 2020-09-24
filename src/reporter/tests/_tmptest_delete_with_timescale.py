from conftest import QL_URL
from exceptions.exceptions import AmbiguousNGSIIdError
from reporter.conftest import create_notification
from reporter.tests.utils import delete_test_data
import json
import pg8000
import pytest
import requests

from translators.timescale import PostgresConnectionData
from translators.sql_translator import SQLTranslator


notify_url = "{}/notify".format(QL_URL)

# TODO: get rid of this file.
# This is just a stopgap solution to re-run the tests in test_delete with
# Timescale. I used my famed C&P tech to lift & tweak code from test_delete.
# Once we have fixed the Timescale queries, the (duplicated) tests in this
# file won't be needed anymore, we should just be able to run the tests in
# test_delete twice, first with Crate as a back-end and then with Timescale
# using the docker compose setup in docker-compose.timescale.yml.


@pytest.fixture(scope='module')
def with_pg8000():
    pg8000.paramstyle = "qmark"
    t = PostgresConnectionData()
    t.read_env()

    conn = pg8000.connect(host=t.host, port=t.port,
                          database=t.db_name,
                          user=t.db_user, password=t.db_pass)
    conn.autocommit = True
    cursor = conn.cursor()

    yield cursor

    cursor.close()
    conn.close()


def count_entity_rows(with_pg8000, service: str, etype: str) -> int:
    table_name = SQLTranslator._et2tn(etype, service)
    stmt = f"SELECT COUNT(*) FROM {table_name}"

    cursor = with_pg8000
    cursor.execute(stmt)
    rows = cursor.fetchall()

    return rows[0][0] if rows else 0


def insert_test_data(service, service_path=None, entity_id=None):
    # 3 entity types, 2 entities for each, 10 updates for each entity.
    for t in ("AirQualityObserved", "Room", "TrafficFlowObserved"):
        for e in range(2):
            for u in range(10):
                ei = entity_id or '{}{}'.format(t, e)
                notification = create_notification(t, ei)
                data = json.dumps(notification)
                h = {
                    'Content-Type': 'application/json',
                    'Fiware-Service': service
                }
                if service_path:
                    h['Fiware-ServicePath'] = service_path
                r = requests.post(notify_url,
                                  data=data,
                                  headers=h)
                assert r.status_code == 200, r.text


def assert_have_all_entities_of_type(etype, service, with_pg8000):
    assert count_entity_rows(with_pg8000, service, etype) == 20


def assert_have_no_entities_of_deleted_id(etype, service, with_pg8000):
    assert count_entity_rows(with_pg8000, service, etype) == 10


def assert_have_no_entities_of_type(etype, service, with_pg8000):
    assert count_entity_rows(with_pg8000, service, etype) == 0


def assert_have_entities_of_type(etype, service, how_many, with_pg8000):
    assert count_entity_rows(with_pg8000, service, etype) == how_many


@pytest.mark.parametrize("service", [
    "t1", "t2"
])
def test_delete_entity(with_pg8000, service):
    """
    By default, delete all records of some entity.
    """
    pass
    insert_test_data(service)

    entity_type = "AirQualityObserved"
    params = {
        'type': entity_type,
    }
    h = {
        'Fiware-Service': service
    }
    url = '{}/entities/{}'.format(QL_URL, entity_type + '0')

    # Values are there
    assert_have_all_entities_of_type(entity_type, service, with_pg8000)

    # Delete them
    r = requests.delete(url, params=params, headers=h)
    assert r.status_code == 204, r.text

    # Values are gone
    # But not for other entities of same type
    assert_have_no_entities_of_deleted_id(entity_type, service, with_pg8000)

    for t in ("AirQualityObserved", "Room", "TrafficFlowObserved"):
        delete_test_data(service, [t])


@pytest.mark.parametrize("service", [
    "t1", "t2"
])
def test_delete_entities(with_pg8000, service):
    """
    By default, delete all historical records of all entities of some type.
    """
    entity_type = "TrafficFlowObserved"
    params = {
        'type': entity_type,
    }
    h = {
        'Fiware-Service': service
    }
    insert_test_data(service)

    # Values are there for both entities
    assert_have_all_entities_of_type(entity_type, service, with_pg8000)

    # 1 Delete call
    url = '{}/types/{}'.format(QL_URL, entity_type)
    r = requests.delete(url, params=params, headers=h)
    assert r.status_code == 204, r.text

    # Values are gone for both entities
    assert_have_no_entities_of_type(entity_type, service, with_pg8000)

    # But not for entities of other types
    assert_have_all_entities_of_type('Room', service, with_pg8000)

    for t in ("AirQualityObserved", "Room"):
        delete_test_data(service, [t])


@pytest.mark.parametrize("service", [
    "t1", "t2"
])
def test_not_found(service):
    entity_type = "AirQualityObserved"
    params = {
        'type': entity_type,
    }
    h = {
        'Fiware-Service': service
    }
    url = '{}/entities/{}'.format(QL_URL, entity_type + '0')

    r = requests.delete(url, params=params, headers=h)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


@pytest.mark.parametrize("service", [
    "t1", "t2"
])
def test_no_type_not_unique(service):
    # If id is not unique across types, you must specify type.
    insert_test_data(service, entity_id='repeatedId')

    url = '{}/entities/{}'.format(QL_URL, 'repeatedId')
    h = {
        'Fiware-Service': service
    }

    # Without type
    r = requests.delete(url, params={}, headers=h)
    assert r.status_code == 409, r.text
    assert r.json() == {
        "error": "AmbiguousNGSIIdError",
        "description": str(AmbiguousNGSIIdError('repeatedId'))
    }

    # With type
    r = requests.delete(url, params={'type': 'AirQualityObserved'}, headers=h)
    assert r.status_code == 204, r.text

    for t in ("AirQualityObserved", "Room", "TrafficFlowObserved"):
        delete_test_data(service, [t])


@pytest.mark.parametrize("service", [
    "t1", "t2"
])
def test_delete_no_type_with_multitenancy(with_pg8000, service):
    """
    A Car and a Truck with the same entity_id. Same thing in two different
    tenants (USA an EU).
    """
    # You have a car1
    car = json.dumps(create_notification("Car", "car1"))

    # In Default
    h_def = {
        'Content-Type': 'application/json',
        'Fiware-Service': service
    }
    r = requests.post(notify_url, data=car, headers=h_def)
    assert r.status_code == 200

    # In EU
    h_eu = {
        'Content-Type': 'application/json',
        'Fiware-Service': 'EU'
    }
    r = requests.post(notify_url, data=car, headers=h_eu)
    assert r.status_code == 200

    # In USA
    h_usa = {
        'Content-Type': 'application/json',
        'Fiware-Service': 'USA'
    }
    r = requests.post(notify_url, data=car, headers=h_usa)
    assert r.status_code == 200

    # I could delete car1 from default without giving a type
    url = '{}/entities/{}'.format(QL_URL, 'car1')
    r = requests.delete(url, params={}, headers=h_def)
    assert r.status_code == 204, r.text

    # But it should still be in EU.
    assert_have_entities_of_type('Car', 'EU', 1, with_pg8000)

    # I could delete car1 from EU without giving a type
    url = '{}/entities/{}'.format(QL_URL, 'car1')
    r = requests.delete(url, params={}, headers=h_eu)
    assert r.status_code == 204, r.text

    # But it should still be in USA.
    assert_have_entities_of_type('Car', 'USA', 1, with_pg8000)

    delete_test_data(service, ["Car"])
    delete_test_data('USA', ["Car"])
    delete_test_data('EU', ["Car"])


def test_delete_347(with_pg8000):
    """
    Test to replicate issue #347.
    """
    entity_type = "deletetestDuno"
    service = 'bbbbb'
    service_path = '/'
    params = {
        'type': entity_type,
    }
    h = {
        'Fiware-Service': service,
        'Fiware-ServicePath': service_path
    }

    data = {
        'subscriptionId': 'ID_FROM_SUB',
        'data': [{
            'id': 'un3',
            'type': 'deletetestDuno',
            'batteryVoltage': {
                'type': 'Text',
                'value': 'ilariso'
            }
        }]
    }

    hn = {
        'Content-Type': 'application/json',
        'Fiware-Service': service,
        'Fiware-ServicePath': service_path
    }
    r = requests.post(notify_url,
                      data=json.dumps(data),
                      headers=hn)
    assert r.status_code == 200, r.text

    # check that value is in the database
    assert_have_entities_of_type(entity_type, service, 1, with_pg8000)

    # Delete call
    url = '{}/types/{}'.format(QL_URL, entity_type)
    r = requests.delete(url, params=params, headers=h)
    assert r.status_code == 204, r.text

    # Values are gone
    assert_have_no_entities_of_type(entity_type, service, with_pg8000)


def test_delete_different_servicepaths(with_pg8000):
    """
    Selective delete by service Path.
    """
    entity_type = "deletetestDuno"
    service = 'bbbbb'
    service_path = '/a'
    params = {
        'type': entity_type,
    }
    h = {
        'Fiware-Service': service,
        'Fiware-ServicePath': service_path
    }

    data = {
        'subscriptionId': 'ID_FROM_SUB',
        'data': [{
            'id': 'un3',
            'type': 'deletetestDuno',
            'batteryVoltage': {
                'type': 'Text',
                'value': 'ilariso'
            }
        }]
    }

    hn = {
        'Content-Type': 'application/json',
        'Fiware-Service': service,
        'Fiware-ServicePath': service_path
    }
    r = requests.post(notify_url,
                      data=json.dumps(data),
                      headers=hn)
    assert r.status_code == 200, r.text

    # insert the same entity in a different service path
    service_path = '/b'
    hn = {
        'Content-Type': 'application/json',
        'Fiware-Service': service,
        'Fiware-ServicePath': service_path
    }
    r = requests.post(notify_url,
                      data=json.dumps(data),
                      headers=hn)
    assert r.status_code == 200, r.text

    # check that value is in the database
    assert_have_entities_of_type(entity_type, service, 2, with_pg8000)

    # Delete /a
    url = '{}/types/{}'.format(QL_URL, entity_type)
    r = requests.delete(url, params=params, headers=h)
    assert r.status_code == 204, r.text

    h = {
        'Fiware-Service': service,
        'Fiware-ServicePath': service_path
    }

    # 1 entity is still there
    assert_have_entities_of_type(entity_type, service, 1, with_pg8000)

    # Delete /b
    url = '{}/types/{}'.format(QL_URL, entity_type)
    r = requests.delete(url, params=params, headers=h)
    assert r.status_code == 204, r.text

    # No entity
    assert_have_no_entities_of_type(entity_type, service, with_pg8000)
