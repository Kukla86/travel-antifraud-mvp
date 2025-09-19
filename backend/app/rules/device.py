from __future__ import annotations
from typing import Dict, Any, Optional
import hashlib
from ..cache import device_cache
from ..config import settings
from pydantic import BaseModel

# Мок-шаблоны подозрительных девайсов (упрощённо)
SUSPICIOUS_PATTERNS = [
    {"platform": "Linux", "userAgent_contains": "Headless"},
    {"platform": "Other", "userAgent_contains": "bot"},
]


class DeviceRuleResult(BaseModel):
    score_delta: int
    fraud_flag: Optional[str] = None


def check_device(device_info: Optional[Dict[str, Any]], user_agent: Optional[str]) -> DeviceRuleResult:
    if not device_info and not user_agent:
        return DeviceRuleResult(score_delta=0, fraud_flag=None)

    # Создаём device fingerprint
    fingerprint_data = {
        "user_agent": (user_agent or "").lower(),
        "platform": str(device_info.get("platform", "")) if device_info else "",
        "screen": device_info.get("screen", {}) if device_info else {},
    }
    fingerprint_str = str(sorted(fingerprint_data.items()))
    fingerprint_hash = hashlib.md5(fingerprint_str.encode()).hexdigest()
    
    # Проверяем частоту использования этого отпечатка
    cache_key = device_cache._make_key("device", fingerprint_hash)
    usage_count = device_cache.get(cache_key) or 0
    device_cache.set(cache_key, usage_count + 1)
    
    # Если отпечаток используется слишком часто - подозрительно
    if usage_count > 10:  # Более 10 использований за час
        return DeviceRuleResult(score_delta=15, fraud_flag="frequent_device_fingerprint")

    ua = (user_agent or "").lower()
    platform = str(device_info.get("platform", "")) if device_info else ""

    for pattern in SUSPICIOUS_PATTERNS:
        p_platform = pattern.get("platform")
        ua_contains = pattern.get("userAgent_contains", "").lower()
        if (not p_platform or p_platform == platform) and (ua_contains in ua):
            return DeviceRuleResult(score_delta=settings.score_device_suspicious, fraud_flag="suspicious_device")

    return DeviceRuleResult(score_delta=0, fraud_flag=None)
    if not device_info and not user_agent:
        return DeviceRuleResult(score_delta=0, fraud_flag=None)

    ua = (user_agent or "").lower()
    platform = str(device_info.get("platform", "")) if device_info else ""

    for pattern in SUSPICIOUS_PATTERNS:
        p_platform = pattern.get("platform")
        ua_contains = pattern.get("userAgent_contains", "").lower()
        if (not p_platform or p_platform == platform) and (ua_contains in ua):
            return DeviceRuleResult(score_delta=10, fraud_flag="suspicious_device")

    return DeviceRuleResult(score_delta=0, fraud_flag=None)
