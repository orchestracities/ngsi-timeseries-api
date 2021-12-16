import pytest

from conftest import REDIS_HOST, REDIS_PORT
from cache import factory
import os


@pytest.fixture()
def enable_geo_caching():
    os.environ["USE_GEOCODING"] = "True"
    os.environ["CACHE_GEOCODING"] = "True"
    yield
    os.environ["USE_GEOCODING"] = "False"
    os.environ["CACHE_GEOCODING"] = "False"


@pytest.fixture()
def enable_query_caching():
    os.environ["CACHE_QUERIES"] = "True"
    yield
    os.environ["CACHE_QUERIES"] = "False"


@pytest.fixture()
def enable_remote_context_caching():
    os.environ["CACHE_REMOTE_CONTEXT"] = "True"
    yield
    os.environ["CACHE_REMOTE_CONTEXT"] = "False"


@pytest.fixture()
def disable_redis():
    del os.environ["REDIS_HOST"]
    yield
    os.environ["REDIS_HOST"] = REDIS_HOST


def test_env_variables_default():
    env = factory.CacheEnvReader()

    assert env.redis_host() == REDIS_HOST
    assert env.redis_port() == REDIS_PORT


def test_get_cache():
    assert factory.get_cache() is not None


def test_get_cache_disabled(disable_redis):
    assert factory.is_cache_available() is False


def test_geo_caching_enabled(enable_geo_caching):
    assert factory.is_geocoding_enabled() is True
    assert factory.is_geo_cache_available() is True


def test_geo_caching_disabled(disable_redis):
    assert factory.is_geocoding_enabled() is False
    assert factory.is_geo_cache_available() is False


def test_get_geo_cache(enable_geo_caching):
    assert factory.get_geo_cache() is not None


def test_query_caching_enabled(enable_query_caching):
    assert factory.is_query_cache_enabled() is True
    assert factory.is_query_cache_available() is True


def test_query_caching_disabled(disable_redis):
    assert factory.is_query_cache_enabled() is False
    assert factory.is_query_cache_available() is False

def test_get_query_cache(enable_query_caching):
    assert factory.get_query_cache() is not None


def test_remote_context_caching_enabled(enable_remote_context_caching):
    assert factory.is_remote_context_cache_enabled() is True
    assert factory.is_remote_context_cache_available() is True


def test_remote_context_caching_disabled(disable_redis):
    assert factory.is_remote_context_cache_enabled() is False
    assert factory.is_remote_context_cache_available() is False


def test_get_remote_context_cache(enable_remote_context_caching):
    assert factory.get_remote_context_cache() is not None
