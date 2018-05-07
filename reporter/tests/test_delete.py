from client.client import HEADERS_PUT
from conftest import QL_URL
from reporter.fixtures import create_notification
import json
import requests
import time


notify_url = "{}/notify".format(QL_URL)


def insert_test_data():
    # 3 entity types, 2 entities for each, 10 updates for each entity.
    for t in ("AirQualityObserved", "Room", "TrafficFlowObserved"):
        for e in range(2):
            for u in range(10):
                notification = create_notification(t, '{}{}'.format(t, e))
                data = json.dumps(notification)
                r = requests.post(notify_url, data=data, headers=HEADERS_PUT)
                assert r.status_code == 200, r.text


def test_delete_entity(clean_crate):
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

    # Values are gone
    time.sleep(1)
    r = requests.get(url, params=params)
    # TODO: Update query API to use 404 in these cases
    assert r.status_code == 200, r.text
    assert r.text == ''

    # But not for other entities of same type
    url = '{}/entities/{}'.format(QL_URL, entity_type+'1')
    r = requests.get(url, params=params)
    assert r.status_code == 200, r.text
    assert r.text != ''


def test_delete_entities(clean_crate):
    """
    By default, delete all historical records of all entities of some type.
    """
    insert_test_data()

    entity_type = "TrafficFlowObserved"
    params = {
        'type': entity_type,
    }

    # Values are there for both entities
    for e in range(2):
        url = '{}/entities/{}'.format(QL_URL, '{}{}'.format(entity_type, e))
        r = requests.get(url, params=params)
        assert r.status_code == 200, r.text
        assert r.text == ''

    # 1 Delete call
    url = '{}/types/{}'.format(QL_URL, entity_type)
    r = requests.delete(url, params=params)
    assert r.status_code == 204, r.text

    # Values are gone for both entities
    time.sleep(1)
    for e in range(2):
        url = '{}/entities/{}'.format(QL_URL, '{}{}'.format(entity_type, e))
        r = requests.get(url, params=params)
        assert r.status_code == 200, r.text
        assert r.text == ''
