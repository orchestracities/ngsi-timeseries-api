import logging
from typing import Union

from utils.cfgreader import EnvReader, BoolVar, IntVar, StrVar, MaybeString

from .querycache import QueryCache
from .geocache import GeoCodingCache
from .rediscache import RedisCache
from aiohttp_client_cache import RedisBackend as ContextCache

MaybeCache = Union[RedisCache, None]
MaybeQueryCache = Union[QueryCache, None]
MaybeGeoCache = Union[GeoCodingCache, None]
MaybeContextCache = Union[ContextCache, None]

REDIS_HOST_ENV_VAR = 'REDIS_HOST'
REDIS_PORT_ENV_VAR = 'REDIS_PORT'
DEFAULT_CACHE_TTL_ENV_VAR = 'DEFAULT_CACHE_TTL'
CACHE_QUERIES_ENV_VAR = 'CACHE_QUERIES'
USE_GEOCODING_ENV_VAR = 'USE_GEOCODING'
CACHE_GEOCODING_ENV_VAR = 'CACHE_GEOCODING'
CACHE_REMOTE_CONTEXT_ENV_VAR = 'CACHE_REMOTE_CONTEXT'

# TODO: it looks like way back then we had a plan to use a config file
# rather than many env vars. In fact I found this comment when refactoring
# the reporter
#   TODO: Move this setting to configuration (See GH issue #10)
# which referred to the below env vars.


class CacheEnvReader:
    """
    Helper class to encapsulate the reading of cache env vars.
    """

    def __init__(self):
        self.env = EnvReader(log=logging.getLogger(__name__).debug)

    def redis_host(self) -> MaybeString:
        return self.env.read(StrVar(REDIS_HOST_ENV_VAR, None))

    def redis_port(self) -> int:
        return self.env.read(IntVar(REDIS_PORT_ENV_VAR, 6379))

    def default_ttl(self) -> int:
        return self.env.read(IntVar(DEFAULT_CACHE_TTL_ENV_VAR, 60))

    def env_reader(self) -> EnvReader:
        return self.env


def log():
    return logging.getLogger(__name__)


def is_query_cache_enabled() -> bool:
    env = CacheEnvReader()
    return env.env_reader().read(BoolVar(CACHE_QUERIES_ENV_VAR, False))


def is_geocoding_enabled() -> bool:
    env = CacheEnvReader()
    return env.env_reader().read(BoolVar(USE_GEOCODING_ENV_VAR, False))


def is_remote_context_cache_enabled() -> bool:
    env = CacheEnvReader()
    return env.env_reader().read(BoolVar(CACHE_REMOTE_CONTEXT_ENV_VAR, False))


def is_geocoding_cache_enabled() -> bool:
    env = CacheEnvReader()
    return env.env_reader().read(BoolVar(CACHE_GEOCODING_ENV_VAR, False))


def is_cache_available() -> bool:
    """
    Can we use cache? Yes if the Redis host env var is set. No otherwise.

    :return: True or False depending on whether or not cache is available.
    """
    env = CacheEnvReader()
    if env.redis_host():
        return True
    return False


def get_cache() -> MaybeCache:
    """
    Build the cache client.

    :return: `None` if `is_cache_available` returns false, a client
        object otherwise.
    """
    env = CacheEnvReader()
    if is_cache_available():
        log().debug("Cache env variables set, building a cache.")
        return RedisCache(env.redis_host(), env.redis_port(),
                          env.default_ttl())

    log().info("Cache is disabled.")
    return None


def is_query_cache_available() -> bool:
    """
    Can we use query cache? Yes if the Redis host env var is set. No otherwise.

    :return: True or False True or False depending on whether or not query
        cache is available.
    """
    env = CacheEnvReader()
    if env.redis_host() and is_query_cache_enabled():
        return True
    return False


def get_query_cache() -> MaybeQueryCache:
    """
    Build the query cache client.

    :return: `None` if `is_query_cache_available` returns false, a client
        object otherwise.
    """
    env = CacheEnvReader()
    if is_query_cache_available():
        log().debug("Cache env variables set, building query cache client.")
        return QueryCache(env.redis_host(), env.redis_port(),
                          env.default_ttl())

    log().info("Query Cache is disabled.")
    return None


def is_geo_cache_available() -> bool:
    """
    Can we use geo-cache? Yes if the "use geo coding" env var is set to
    true and the Redis host env var is set. No otherwise. The idea is that
    we can only use geo coding when we also have a Redis cache to go with
    it.

    :return: True or False depending on whether or not we're supposed to
        use geo-cache.
    """
    env = CacheEnvReader()
    if env.redis_host() and is_geocoding_enabled():
        return True
    return False


def get_geo_cache() -> MaybeGeoCache:
    """
    Build the geo cache client.

    :return: `None` if `is_geo_coding_available` returns false, a client
        object otherwise.
    """
    env = CacheEnvReader()
    if is_geo_cache_available():
        return GeoCodingCache(env.redis_host(), env.redis_port())

    log().warning("Geo Cache is not enabled, check env variables.")
    return None


def is_remote_context_cache_available() -> bool:
    """
    Can we use geo-cache? Yes if the "use geo coding" env var is set to
    true and the Redis host env var is set. No otherwise. The idea is that
    we can only use geo coding when we also have a Redis cache to go with
    it.

    :return: True or False depending on whether or not we're supposed to
        use geo-cache.
    """
    env = CacheEnvReader()
    if env.redis_host() and is_remote_context_cache_enabled():
        return True
    return False


def get_remote_context_cache() -> MaybeContextCache:
    """
    Build the remote ngsild context cache client.

    :return: `None` if `is_geo_coding_available` returns false, a client
        object otherwise.
    """
    env = CacheEnvReader()
    if is_remote_context_cache_enabled():
        #TODO do we need custom ttl for different caches?
        return ContextCache('context-cache', address='redis://' + env.redis_host() + ':' + str(env.redis_port()), expire_after=env.default_ttl())

    log().warning("Cache for remote NGSI-LD context is not enabled.")
    return None