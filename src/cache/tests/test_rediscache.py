import json
from time import sleep

from conftest import REDIS_HOST, REDIS_PORT
from cache.rediscache import RedisCache
import pytest


def test_insert(docker_redis):
    cache = RedisCache(REDIS_HOST, REDIS_PORT, 0)

    key1 = "insert/entityType/type"
    key2 = "/v2/entities/type"

    value1 = 'string'
    value2 = 2

    cache.put(key1, value1)
    cache.put(key2, value2)

    assert cache.get(key1) == value1
    assert int(cache.get(key2)) == int(value2)

    cache.flushall()


def test_expire(docker_redis):
    cache = RedisCache(REDIS_HOST, REDIS_PORT, 0)

    key = "insert/entityType/type"
    value = 'string'

    cache.put(key, value, 1)
    assert cache.get(key) == value
    cache.expire(key)
    assert cache.get(key) is None

    cache.flushall()


def test_delete(docker_redis):
    cache = RedisCache(REDIS_HOST, REDIS_PORT, 0)

    key = "insert/entityType/type"
    value = 'string'

    cache.put(key, value)
    assert cache.get(key) == value
    cache.delete(key)
    assert cache.get(key) is None

    cache.flushall()


def test_health_ok(docker_redis):
    cache = RedisCache(REDIS_HOST, REDIS_PORT, 0)
    assert cache.get_health()['status'] == 'pass'


def test_health_ko(docker_redis, docker_services):
    cache = RedisCache(REDIS_HOST, REDIS_PORT, 0)
    docker_services.shutdown()
    assert cache.get_health()['status'] == 'fail'
