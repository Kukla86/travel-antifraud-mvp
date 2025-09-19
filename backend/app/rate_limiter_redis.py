from typing import Optional
from datetime import datetime, timedelta
import asyncio
from .redis_client import redis_client

class RedisRateLimiter:
    def __init__(self):
        self.redis = redis_client
    
    async def is_allowed(self, key: str, limit: int, window_minutes: int = 1) -> bool:
        """Проверяет, разрешён ли запрос для ключа в пределах лимита за окно."""
        if not self.redis.redis:
            return True  # Fallback если Redis недоступен
        
        try:
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(minutes=window_minutes)
            
            # Используем sliding window с Redis
            pipe = self.redis.redis.pipeline()
            
            # Удаляем старые записи
            pipe.zremrangebyscore(key, 0, window_start.timestamp())
            
            # Подсчитываем текущие запросы
            pipe.zcard(key)
            
            # Добавляем текущий запрос
            pipe.zadd(key, {str(current_time.timestamp()): current_time.timestamp()})
            
            # Устанавливаем TTL
            pipe.expire(key, window_minutes * 60)
            
            results = await pipe.execute()
            current_count = results[1]
            
            return current_count < limit
            
        except Exception as e:
            print(f"Redis rate limiter error: {e}")
            return True  # Fallback при ошибке
    
    async def get_remaining_requests(self, key: str, limit: int, window_minutes: int = 1) -> int:
        """Получить количество оставшихся запросов."""
        if not self.redis.redis:
            return limit
        
        try:
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(minutes=window_minutes)
            
            # Удаляем старые записи
            await self.redis.redis.zremrangebyscore(key, 0, window_start.timestamp())
            
            # Подсчитываем текущие запросы
            current_count = await self.redis.redis.zcard(key)
            
            return max(0, limit - current_count)
            
        except Exception:
            return limit

# Глобальный rate limiter
redis_rate_limiter = RedisRateLimiter()
