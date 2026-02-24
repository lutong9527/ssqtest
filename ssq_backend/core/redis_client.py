import redis
from core.config import settings


class RedisClient:

    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )

    def get(self, key):
        return self.client.get(key)

    def set(self, key, value, ex=None):
        self.client.set(key, value, ex=ex)

    def incr(self, key):
        return self.client.incr(key)

    def expire(self, key, ttl):
        self.client.expire(key, ttl)


redis_client = RedisClient()
