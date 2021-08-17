import pytest

from conftest import REDIS_HOST, REDIS_PORT
from geocoding import factory
import os


@pytest.fixture()
def enable_geo_caching():
    os.environ["USE_GEOCODING"] = "True"
    os.environ["CACHE_GEOCODING"] = "True"
    yield
    os.environ["USE_GEOCODING"] = "False"
    os.environ["CACHE_GEOCODING"] = "False"


@pytest.fixture()
def disable_redis():
    del os.environ["REDIS_HOST"]
    yield
    os.environ["REDIS_HOST"] = REDIS_HOST


def test_env_variables_default():
    env = factory.GeoCodingEnvReader()

    assert env.use_geocoding() is False
    assert env.cache_geocoding() is False
    assert env.redis_host() == REDIS_HOST
    assert env.redis_port() == REDIS_PORT


def test_env_variables_geo_caching_enabled(enable_geo_caching):
    env = factory.GeoCodingEnvReader()

    assert env.use_geocoding() is True
    assert env.cache_geocoding() is True


def test_geo_caching_enabled(enable_geo_caching):
    assert factory.is_geo_coding_available() is True
    assert factory.is_geo_cache_available() is True


def test_geo_caching_disabled(disable_redis):
    assert factory.is_geo_coding_available() is False
    assert factory.is_geo_cache_available() is False


def test_get_geo_cache(enable_geo_caching):
    assert factory.get_geo_cache() is not None
