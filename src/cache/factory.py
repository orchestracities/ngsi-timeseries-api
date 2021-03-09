import logging
from typing import Union

from utils.cfgreader import EnvReader, BoolVar, IntVar, StrVar, MaybeString

from .querycache import QueryCache

MaybeCache = Union[QueryCache, None]


REDIS_HOST_ENV_VAR = 'REDIS_HOST'
REDIS_PORT_ENV_VAR = 'REDIS_PORT'
DEFAULT_CACHE_TTL_ENV_VAR = 'DEFAULT_CACHE_TTL'
CACHE_QUERIES_ENV_VAR = 'CACHE_QUERIES'


class CacheEnvReader:
    """
    Helper class to encapsulate the reading of geo-coding env vars.
    """

    def __init__(self):
        self.env = EnvReader(log=logging.getLogger(__name__).debug)

    def redis_host(self) -> MaybeString:
        return self.env.read(StrVar(REDIS_HOST_ENV_VAR, None))

    def redis_port(self) -> int:
        return self.env.read(IntVar(REDIS_PORT_ENV_VAR, 6379))

    def default_ttl(self) -> int:
        return self.env.read(IntVar(DEFAULT_CACHE_TTL_ENV_VAR, 60))

    def cache_queries(self) -> bool:
        return self.env.read(BoolVar(CACHE_QUERIES_ENV_VAR, False))


def log():
    return logging.getLogger(__name__)


def is_cache_available() -> bool:
    """
    Can we use cache? Yes if the Redis host env var is set. No otherwise.

    :return: True or False depending on whether or not we're supposed to
        use geo-coding.
    """
    env = CacheEnvReader()
    if env.redis_host() and env.cache_queries():
        return True
    return False


def get_cache() -> MaybeCache:
    """
    Build the geo cache client.

    :return: `None` if `is_cache_available` returns false, a client
        object otherwise.
    """
    env = CacheEnvReader()
    if is_cache_available():
        log().debug("Cache env variables set, building a cache.")
        return QueryCache(env.redis_host(), env.redis_port(),
                          env.default_ttl())

    log().info("Cache env variables indicate cache should not be used.")
    return None
