from client.fixtures import orion_client as orion, clean_mongo, entity
from random import random
from utils.common import create_simple_subscription, create_simple_subscription_v1
import json
import pytest


def test_version(orion):
    r = orion.version()
    assert r.ok, r.text
    assert '"version" : "1.7.0"' in r.text


def test_subscribe(orion, clean_mongo):
    notify_url = "http://somewhere/notify"
    subscription = create_simple_subscription(notify_url)

    r = orion.subscribe(subscription)
    assert r.ok, r.text
    assert r.status_code == 201

    r = orion.get('subscriptions')
    assert r.ok
    assert r.status_code == 200

    subs = json.loads(r.text)
    assert len(subs) == 1


def test_subscribe_v1(orion, clean_mongo):
    notify_url = "http://somewhere/notify"
    subscription = create_simple_subscription_v1(notify_url)
    r = orion.subscribe_v1(subscription)
    assert r.ok
    assert r.status_code == 200

    r = orion.get('subscriptions')
    assert r.ok
    assert r.status_code == 200

    subs = json.loads(r.text)
    assert len(subs) == 1


def test_insert(orion, clean_mongo, entity):
    r = orion.insert(entity)
    assert r.ok, r.text


def test_get(orion, clean_mongo, entity):
    r = orion.insert(entity)
    assert r.ok

    r = orion.get('entities')
    loaded_entities = json.loads(r.text)
    assert len(loaded_entities) == 1

    assert loaded_entities[0] == entity


def test_update(orion, clean_mongo, entity):
    r = orion.insert(entity)
    assert r.ok

    v = 10 + 30 * random()
    attrs = {'temperature': {
        'value': v,
        'type': 'Float'
    }}
    r = orion.update(entity['id'], attrs)
    assert r.ok

    r = orion.get('entities')
    assert r.ok

    loaded_entities = json.loads(r.text)
    loaded_v = loaded_entities[0]['temperature']['value']
    assert loaded_v == pytest.approx(v)


def test_delete(orion, clean_mongo, entity):
    r = orion.insert(entity)
    assert r.ok

    r = orion.delete(entity['id'])
    print(r.ok)
    print(r.text)

    r = orion.get('entities')
    loaded_entities = json.loads(r.text)
    assert len(loaded_entities) == 0
