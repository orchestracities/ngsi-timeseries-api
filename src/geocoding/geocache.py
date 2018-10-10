from datetime import datetime


class GeoCodingCache(object):

    def __init__(self, redis_host, redis_port):
        import redis
        self.redis = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            db=0,
            decode_responses=True
        )

    def get(self, key):
        return self.redis.get(key)

    def put(self, key, value):
        self.redis.set(key, value)

    def get_health(self):
        """
        :return: dictionary with redis service health. ::see:: reporter.health.
        """
        import redis

        res = {}
        res['time'] = datetime.now().isoformat()
        try:
            r = self.redis.ping()
        except (redis.exceptions.ConnectionError,
                redis.exceptions.TimeoutError,
                redis.exceptions.RedisError) as e:
            res['status'] = 'fail'
            res['output'] = "{}".format(e)
        else:
            if r:
                res['status'] = 'pass'
            else:
                res['status'] = 'warn'
                res['output'] = "Redis is not playing ping pong :/"
        return res


def temp_geo_cache(host, port):
    gc = GeoCodingCache(host, port)
    try:
        yield gc
    finally:
        gc.redis.flushall()

