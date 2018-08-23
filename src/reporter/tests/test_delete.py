from conftest import QL_URL, crate_translator as translator
from exceptions.exceptions import AmbiguousNGSIIdError
from reporter.conftest import create_notification
import json
import requests

notify_url = "{}/notify".format(QL_URL)


def insert_test_data(entity_id=None):
    # 3 entity types, 2 entities for each, 10 updates for each entity.
    for t in ("AirQualityObserved", "Room", "TrafficFlowObserved"):
        for e in range(2):
            for u in range(10):
                ei = entity_id or '{}{}'.format(t, e)
                notification = create_notification(t, ei)
                data = json.dumps(notification)
                h = {'Content-Type': 'application/json'}
                r = requests.post(notify_url,
                                  data=data,
                                  headers=h)
                assert r.status_code == 200, r.text


def test_delete_entity(translator):
    """
    By default, delete all records of some entity.
    """
    insert_test_data()

    entity_type = "AirQualityObserved"
    params = {
        'type': entity_type,
    }
    url = '{}/entities/{}'.format(QL_URL, entity_type+'0')

    # Values are there
    r = requests.get(url, params=params)
    assert r.status_code == 200, r.text
    assert r.text != ''

    # Delete them
    r = requests.delete(url, params=params)
    assert r.status_code == 204, r.text
    translator._refresh([entity_type])

    # Values are gone
    r = requests.get(url, params=params)
    assert r.status_code == 404, r.text

    # But not for other entities of same type
    url = '{}/entities/{}'.format(QL_URL, entity_type+'1')
    r = requests.get(url, params=params)
    assert r.status_code == 200, r.text
    assert r.text != ''


def test_delete_entities(translator):
    """
    By default, delete all historical records of all entities of some type.
    """
    entity_type = "TrafficFlowObserved"
    params = {
        'type': entity_type,
    }

    insert_test_data()
    translator._refresh([entity_type, "Room"])

    # Values are there for both entities
    for e in range(2):
        url = '{}/entities/{}'.format(QL_URL, '{}{}'.format(entity_type, e))
        r = requests.get(url, params=params)
        assert r.status_code == 200, r.text
        assert r.text != ''

    # 1 Delete call
    url = '{}/types/{}'.format(QL_URL, entity_type)
    r = requests.delete(url, params=params)
    assert r.status_code == 204, r.text

    # Values are gone for both entities
    for e in range(2):
        url = '{}/entities/{}'.format(QL_URL, '{}{}'.format(entity_type, e))
        r = requests.get(url, params=params)
        assert r.status_code == 404, r.text

    # But not for entities of other types
    url = '{}/entities/{}'.format(QL_URL, 'Room1')
    r = requests.get(url, params={'type': 'Room'})
    assert r.status_code == 200, r.text
    assert r.text != ''


def test_not_found():
    entity_type = "AirQualityObserved"
    params = {
        'type': entity_type,
    }
    url = '{}/entities/{}'.format(QL_URL, entity_type+'0')

    r = requests.delete(url, params=params)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


def test_no_type_not_unique(translator):
    # If id is not unique across types, you must specify type.
    insert_test_data(entity_id='repeatedId')
    translator._refresh(['AirQualityObserved'])

    url = '{}/entities/{}'.format(QL_URL, 'repeatedId')

    # Without type
    r = requests.delete(url, params={})
    assert r.status_code == 409, r.text
    assert r.json() == {
        "error": "AmbiguousNGSIIdError",
        "description": str(AmbiguousNGSIIdError('repeatedId'))
    }

    # With type
    r = requests.delete(url, params={'type': 'AirQualityObserved'})
    assert r.status_code == 204, r.text


def test_delete_no_type_with_multitenancy(translator):
    """
    A Car and a Truck with the same entity_id. Same thing in two different
    tenants (USA an EU).
    """
    # You have a car1
    car = json.dumps(create_notification("Car", "car1"))

    # In Default
    h_def = {'Content-Type': 'application/json'}
    r = requests.post(notify_url, data=car, headers=h_def)
    assert r.status_code == 200
    translator._refresh(['Car'])

    # In EU
    h_eu = {
        'Content-Type': 'application/json',
        'Fiware-Service': 'EU'
    }
    r = requests.post(notify_url, data=car, headers=h_eu)
    assert r.status_code == 200
    translator._refresh(['Car'], fiware_service='EU')

    # In USA
    h_usa = {
        'Content-Type': 'application/json',
        'Fiware-Service': 'USA'
    }
    r = requests.post(notify_url, data=car, headers=h_usa)
    assert r.status_code == 200
    translator._refresh(['Car'], fiware_service='USA')

    # I could delete car1 from default without giving a type
    url = '{}/entities/{}'.format(QL_URL, 'car1')
    r = requests.delete(url, params={}, headers=h_def)
    assert r.status_code == 204, r.text

    # But it should still be in EU.
    r = requests.get(url, params={}, headers=h_eu)
    assert r.status_code == 200, r.text

    # I could delete car1 from EU without giving a type
    url = '{}/entities/{}'.format(QL_URL, 'car1')
    r = requests.delete(url, params={}, headers=h_eu)
    assert r.status_code == 204, r.text
    translator._refresh(['Car'], fiware_service='EU')

    # But it should still be in USA.
    r = requests.get(url, params={}, headers=h_usa)
    assert r.status_code == 200, r.text
