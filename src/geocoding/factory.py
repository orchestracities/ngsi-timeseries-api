import logging
from typing import Union

from .geocache import GeoCodingCache
from utils.cfgreader import EnvReader, BoolVar, IntVar, StrVar, MaybeString


MaybeGeoCache = Union[GeoCodingCache, None]


# TODO: it looks like way back then we had a plan to use a config file
# rather than many env vars. In fact I found this comment when refactoring
# the reporter
#   TODO: Move this setting to configuration (See GH issue #10)
# which referred to the below env vars.


class GeoCodingEnvReader:
    """
    Helper class to encapsulate the reading of geo-coding env vars.
    """

    def __init__(self):
        self.env = EnvReader(log=logging.getLogger(__name__).info)

    def use_geocoding(self) -> bool:
        return self.env.read(BoolVar('USE_GEOCODING', False))

    def redis_host(self) -> MaybeString:
        return self.env.read(StrVar('REDIS_HOST', None))

    def redis_port(self) -> int:
        return self.env.read(IntVar('REDIS_PORT', 6379))


def log():
    return logging.getLogger(__name__)


def is_geo_coding_available() -> bool:
    """
    Can we use geo-coding? Yes if the "use geo coding" env var is set to
    true and the Redis host env var is set. No otherwise. The idea is that
    we can only use geo coding when we also have a Redis cache to go with
    it.

    :return: True or False depending on whether or not we're supposed to
        use geo-coding.
    """
    env = GeoCodingEnvReader()
    if env.use_geocoding() and env.redis_host():
        return True
    return False


def get_geo_cache() -> MaybeGeoCache:
    """
    Build the geo cache client.

    :return: `None` if `is_geo_coding_available` returns false, a client
        object otherwise.
    """
    env = GeoCodingEnvReader()
    if is_geo_coding_available():
        log().info("Geo Cache env variables set, building a cache.")

        return GeoCodingCache(env.redis_host(), env.redis_port())

    log().info("Geo Cache env variables indicate cache should not be used.")
    return None
