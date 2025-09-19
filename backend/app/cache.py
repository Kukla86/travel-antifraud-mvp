from __future__ import annotations
from typing import Any, Optional
from datetime import datetime, timedelta
import threading
import hashlib
import json


class SimpleCache:
    def __init__(self, ttl_hours: int = 24):
        self._lock = threading.Lock()
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._ttl = timedelta(hours=ttl_hours)
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            
            value, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp > self._ttl:
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._cache[key] = (value, datetime.utcnow())
    
    def cleanup(self) -> None:
        """Удаляет устаревшие записи."""
        now = datetime.utcnow()
        with self._lock:
            expired_keys = [
                key for key, (_, timestamp) in self._cache.items()
                if now - timestamp > self._ttl
            ]
            for key in expired_keys:
                del self._cache[key]
    
    def _make_key(self, prefix: str, data: str) -> str:
        """Создаёт ключ кэша на основе префикса и данных."""
        return f"{prefix}:{hashlib.md5(data.encode()).hexdigest()}"


# Глобальные кэши
geo_cache = SimpleCache(ttl_hours=24)
bin_cache = SimpleCache(ttl_hours=24)
device_cache = SimpleCache(ttl_hours=1)  # Короткий TTL для device fingerprint
