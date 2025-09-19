import redis.asyncio as redis
from typing import Optional, Any
import json
from .config import settings

class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Подключение к Redis."""
        try:
            self.redis = redis.from_url("redis://localhost:6379", decode_responses=True)
            await self.redis.ping()
            print("Connected to Redis")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.redis = None
    
    async def disconnect(self):
        """Отключение от Redis."""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из Redis."""
        if not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Установить значение в Redis с TTL."""
        if not self.redis:
            return
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception:
            pass
    
    async def delete(self, key: str):
        """Удалить ключ из Redis."""
        if not self.redis:
            return
        try:
            await self.redis.delete(key)
        except Exception:
            pass
    
    async def increment(self, key: str, ttl: int = 3600) -> int:
        """Инкремент с TTL."""
        if not self.redis:
            return 0
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = await pipe.execute()
            return results[0]
        except Exception:
            return 0

# Глобальный клиент Redis
redis_client = RedisClient()
