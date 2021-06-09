from datetime import datetime


class RedisCache(object):

    def __init__(
            self,
            redis_host,
            redis_port,
            redis_db,
            decode_responses=True):
        import redis
        self.redis = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=decode_responses
        )

    def get(self, key):
        return self.redis.get(key)

    def put(self, key, value, ex=None):
        self.redis.set(key, value, ex=ex)

    def expire(self, key, ex=0):
        self.redis.expire(key, ex)

    def delete(self, key):
        self.redis.delete(key)

    def flushall(self):
        self.redis.flushall()

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
