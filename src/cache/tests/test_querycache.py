import json
from time import sleep

from conftest import REDIS_HOST, REDIS_PORT
from cache.querycache import QueryCache
import pytest


def test_insert():
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

    assert cache.get(table_name, key1) == str(value1)
    assert cache.get(table_name, key2) == str(value2)

    cache.flushall()


def test_expire():
    cache = QueryCache(REDIS_HOST, REDIS_PORT)

    table_name = "test table"
    key = "insert/entityType/type"
    value = 'string'

    cache.put(table_name, key, value, 1)
    assert cache.get(table_name, key) == str(value)
    sleep(5)
    assert cache.get(table_name, key) is None

    cache.flushall()


def test_delete():
    cache = QueryCache(REDIS_HOST, REDIS_PORT)

    table_name = "test table"
    key = "insert/entityType/type"
    value = 'string'

    cache.put(table_name, key, value)
    assert cache.get(table_name, key) == str(value)
    cache.delete(table_name, key)
    assert cache.get(table_name, key) is None

    cache.flushall()
