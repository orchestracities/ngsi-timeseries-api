import json
from time import sleep

from conftest import REDIS_HOST, REDIS_PORT
from cache.querycache import QueryCache
import pytest


def test_insert(docker_redis):
    cache = QueryCache(REDIS_HOST, REDIS_PORT)

    table_name = "test table"
    key1 = "insert/entityType/type"
    key2 = "/v2/entities/type"

    value1 = 'string'
    value2 = {
        'dic': 2
    }

    cache.put(table_name, key1, value1)
    cache.put(table_name, key2, value2)

    assert cache.get(table_name, key1) == value1
    assert cache.get(table_name, key2) == value2

    cache.flushall()


def test_expire(docker_redis):
    cache = QueryCache(REDIS_HOST, REDIS_PORT)

    table_name = "test table"
    key = "insert/entityType/type"
    value = 'string'

    cache.put(table_name, key, value, 1)
    assert cache.get(table_name, key) == value
    sleep(2)
    assert cache.get(table_name, key) is None

    cache.flushall()


def test_delete(docker_redis):
    cache = QueryCache(REDIS_HOST, REDIS_PORT)

    table_name = "test table"
    key = "insert/entityType/type"
    value = 'string'

    cache.put(table_name, key, value)
    assert cache.get(table_name, key) == value
    cache.delete(table_name, key)
    assert cache.get(table_name, key) is None

    cache.flushall()


def test_null_tenant(docker_redis):
    cache = QueryCache(REDIS_HOST, REDIS_PORT)

    table_name = None
    key1 = "insert/entityType/type"
    key2 = "/v2/entities/type"

    value1 = 'string'
    value2 = {
        'dic': 2
    }

    cache.put(table_name, key1, value1)
    cache.put(table_name, key2, value2)

    assert cache.get(table_name, key1) == value1
    assert cache.get(table_name, key2) == value2

    cache.flushall()


def test_null_key(docker_redis):
    cache = QueryCache(REDIS_HOST, REDIS_PORT)

    table_name = ""
    key1 = "insert/entityType/type"
    key2 = ""

    value1 = 'string'
    value2 = {
        'dic': 2
    }

    cache.put(table_name, key1, value1)
    cache.put(table_name, key2, value2)

    assert cache.get(table_name, key1) == value1
    assert cache.get(table_name, key2) == value2

    cache.flushall()


def test_null_value(docker_redis):
    cache = QueryCache(REDIS_HOST, REDIS_PORT)

    table_name = "test table"
    key1 = "insert/entityType/type"
    key2 = "/v2/entities/type"

    value1 = 'string'
    value2 = None

    cache.put(table_name, key1, value1)
    cache.put(table_name, key2, value2)

    assert cache.get(table_name, key1) == value1
    assert cache.get(table_name, key2) == value2

    cache.flushall()
