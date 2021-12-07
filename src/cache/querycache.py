from datetime import datetime
from cache import rediscache
import pickle


class QueryCache(rediscache.RedisCache):

    @staticmethod
    def xstr(s):
        if s is None:
            return ''
        return str(s)

    def __init__(self, redis_host, redis_port, default_ttl=60):
        self.default_ttl = default_ttl
        super(QueryCache, self).__init__(redis_host, redis_port, 1, False)

    def get(self, tenant_name, key):
        value = self.redis.hget(':' + self.xstr(tenant_name), key)
        if value:
            res = pickle.loads(value)
            return res
        return None

    def exists(self, tenant_name, key):
        return self.redis.hexists(':' + self.xstr(tenant_name), key)

    def put(self, tenant_name, key, value, ex=None):
        if value is not None:
            value = pickle.dumps(value)
            self.redis.hset(':' + self.xstr(tenant_name), key, value)
            if ex:
                # unfortunately redis does not support expiration for single keys
                # inside an hset, so we set expiration for the whole hset
                self.redis.expire(':' + self.xstr(tenant_name), ex)

    def delete(self, tenant_name, key):
        self.redis.hdel(':' + self.xstr(tenant_name), key)
