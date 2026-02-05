import redis
from app.config import settings

class RedisCache:
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    def get_url(self, short_code: str) -> str | None:
        return self.client.get(f"link:{short_code}")
    
    def set_url(self, short_code: str, original_url: str, expire_seconds: int = 3600):
        self.client.setex(f"link:{short_code}", expire_seconds, original_url)
    
    def increment_clicks(self, short_code: str):
        self.client.incr(f"clicks:{short_code}")

cache = RedisCache()