from __future__ import annotations
from typing import Dict, Tuple
from datetime import datetime, timedelta
import threading
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, key: str, limit: int, window_minutes: int = 1) -> bool:
        """Проверяет, разрешён ли запрос для ключа в пределах лимита за окно."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=window_minutes)
        
        with self._lock:
            requests = self._requests[key]
            
            # Удаляем старые запросы
            while requests and requests[0] < cutoff:
                requests.popleft()
            
            # Проверяем лимит
            if len(requests) >= limit:
                return False
            
            # Добавляем текущий запрос
            requests.append(now)
            return True
    
    def cleanup_old_entries(self, max_age_hours: int = 24):
        """Очищает старые записи для экономии памяти."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        with self._lock:
            for key in list(self._requests.keys()):
                requests = self._requests[key]
                while requests and requests[0] < cutoff:
                    requests.popleft()
                
                if not requests:
                    del self._requests[key]


# Глобальный экземпляр
rate_limiter = RateLimiter()
