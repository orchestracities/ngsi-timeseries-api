from datetime import datetime
from cache import rediscache


class GeoCodingCache(rediscache.RedisCache):

    def __init__(self, redis_host, redis_port):
        super(GeoCodingCache, self).__init__(redis_host, redis_port, 0)


def temp_geo_cache(host, port):
    gc = GeoCodingCache(host, port)
    try:
        yield gc
    finally:
        gc.redis.flushall()
