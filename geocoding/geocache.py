

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
