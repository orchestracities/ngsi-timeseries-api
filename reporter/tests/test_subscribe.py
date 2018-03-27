from client.fixtures import clean_mongo
from conftest import QL_URL, ORION_URL
import requests

subscribe_url = "{}/subscribe".format(QL_URL)


def test_invalid_wrong_orion_url():
    params = {
        'orionUrl': "blabla",
        'quantumleapUrl': "quantumleap",
    }
    r = requests.post(subscribe_url, params=params)
    assert r.status_code == 412
    assert r.json() == "Orion is not reachable by QuantumLeap at blabla. " \
                       "Fix your orionUrl."


def test_valid_defaults(clean_mongo):
    params = {
        'orionUrl': ORION_URL,
        'quantumleapUrl': QL_URL,
    }
    r = requests.post(subscribe_url, params=params)
    assert r.status_code == 201

    # Check created subscription
    r = requests.get("{}/subscriptions".format(ORION_URL))
    assert r.ok
    res = r.json()
    assert len(res) == 1
    subscription = res[0]

    assert subscription['description'] == 'Created by QuantumLeap {}.' \
                                          ''.format(QL_URL)
    assert subscription['subject'] == {
        'entities': [{'idPattern': '.*'}],
        'condition': {'attrs': []}
    }
    assert subscription['notification'] == {
        'attrs': [],
        'attrsFormat': 'normalized',
        'http': {'url': "{}/notify".format(QL_URL)},
        'metadata': ['dateCreated', 'dateModified'],
    }
    assert subscription['throttling'] == 1


def test_valid_customs(clean_mongo):
    params = {
        'orionUrl': ORION_URL,
        'quantumleapUrl': QL_URL,
        'entityType': "Room",
        'idPattern': "Room1",
        'attributes': "temperature,pressure",
        'fiwareService': "default",
        'fiwareServicepath': "/custom",
    }
    r = requests.post(subscribe_url, params=params)
    assert r.status_code == 201

    # Check created subscription
    headers = {
        'fiware-service': "default",
        'fiware-servicepath': "/custom",
    }
    r = requests.get("{}/subscriptions".format(ORION_URL), headers=headers)
    assert r.ok
    res = r.json()
    assert len(res) == 1
    subscription = res[0]

    assert subscription['description'] == 'Created by QuantumLeap {}.' \
                                          ''.format(QL_URL)
    assert subscription['subject'] == {
        'entities': [{'idPattern': 'Room1', 'type': 'Room'}],
        'condition': {'attrs': ["temperature", "pressure"]}
    }
    assert subscription['notification'] == {
        'attrs': ["temperature", "pressure"],
        'attrsFormat': 'normalized',
        'http': {'url': "{}/notify".format(QL_URL)},
        'metadata': ['dateCreated', 'dateModified'],
    }
    assert subscription['throttling'] == 1
