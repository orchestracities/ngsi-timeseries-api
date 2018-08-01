from conftest import QL_URL
from reporter.conftest import create_notification
from conftest import crate_translator as translator
import json
import requests

notify_url = "{}/notify".format(QL_URL)


def insert_test_data():
    # 3 entity types, 2 entities for each, 10 updates for each entity.
    for t in ("AirQualityObserved", "Room", "TrafficFlowObserved"):
        for e in range(2):
            for u in range(10):
                notification = create_notification(t, '{}{}'.format(t, e))
                data = json.dumps(notification)
                r = requests.post(notify_url,
                                  data=data,
                                  headers={'Content-Type':'application/json'})
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


def test_tmp_no_type():
    """
    For now specifying entity type is mandatory
    """
    entity_type = "TrafficFlowObserved"
    url = '{}/entities/{}'.format(QL_URL, entity_type+'0')
    r = requests.delete(url, params={})

    assert r.status_code == 400, r.text
    assert r.json() == {
        "error": "Not Implemented",
        "description": "For now, you must always specify entity type."
    }
