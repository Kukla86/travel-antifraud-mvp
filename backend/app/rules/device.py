from __future__ import annotations
from typing import Dict, Any, Optional, List
import hashlib
import re
from ..cache import device_cache
from ..config import settings
from pydantic import BaseModel

# Расширенные паттерны подозрительных устройств
SUSPICIOUS_PATTERNS = [
    {"platform": "Linux", "userAgent_contains": "Headless"},
    {"platform": "Other", "userAgent_contains": "bot"},
    {"platform": "Other", "userAgent_contains": "crawler"},
    {"platform": "Other", "userAgent_contains": "spider"},
    {"platform": "Other", "userAgent_contains": "scraper"},
    {"platform": "Other", "userAgent_contains": "selenium"},
    {"platform": "Other", "userAgent_contains": "phantom"},
    {"platform": "Other", "userAgent_contains": "puppeteer"},
    {"platform": "Other", "userAgent_contains": "playwright"},
    {"platform": "Other", "userAgent_contains": "automation"},
    {"platform": "Other", "userAgent_contains": "test"},
    {"platform": "Other", "userAgent_contains": "headless"},
]

# Подозрительные User-Agent паттерны
SUSPICIOUS_UA_PATTERNS = [
    r'bot|spider|crawler|scraper|selenium|phantom|puppeteer|playwright|automation|test|headless',
    r'python|java|curl|wget|http|request|client|library|framework',
    r'^$',  # Пустой User-Agent
    r'^.{1,10}$',  # Очень короткий User-Agent
    r'^.{200,}$',  # Очень длинный User-Agent
]

# Подозрительные screen resolutions
SUSPICIOUS_SCREEN_RESOLUTIONS = [
    {"width": 0, "height": 0},  # Нулевое разрешение
    {"width": 1, "height": 1},  # Минимальное разрешение
    {"width": 800, "height": 600},  # Старое разрешение
    {"width": 1024, "height": 768},  # Старое разрешение
]


class DeviceRuleResult(BaseModel):
    score_delta: int
    fraud_flag: Optional[str] = None


def check_device(device_info: Optional[Dict[str, Any]], user_agent: Optional[str]) -> DeviceRuleResult:
    if not device_info and not user_agent:
        return DeviceRuleResult(score_delta=0, fraud_flag=None)

    ua = (user_agent or "").lower()
    platform = str(device_info.get("platform", "")) if device_info else ""
    screen = device_info.get("screen", {}) if device_info else {}

    # Проверяем подозрительные User-Agent паттерны
    for pattern in SUSPICIOUS_UA_PATTERNS:
        if re.search(pattern, ua, re.IGNORECASE):
            return DeviceRuleResult(score_delta=settings.score_device_suspicious, fraud_flag="suspicious_user_agent")

    # Проверяем подозрительные screen resolutions
    screen_width = screen.get("width", 0)
    screen_height = screen.get("height", 0)
    for suspicious_res in SUSPICIOUS_SCREEN_RESOLUTIONS:
        if (screen_width == suspicious_res["width"] and 
            screen_height == suspicious_res["height"]):
            return DeviceRuleResult(score_delta=settings.score_device_suspicious, fraud_flag="suspicious_screen_resolution")

    # Проверяем старые паттерны
    for pattern in SUSPICIOUS_PATTERNS:
        p_platform = pattern.get("platform")
        ua_contains = pattern.get("userAgent_contains", "").lower()
        if (not p_platform or p_platform == platform) and (ua_contains in ua):
            return DeviceRuleResult(score_delta=settings.score_device_suspicious, fraud_flag="suspicious_device")

    # Создаём device fingerprint
    fingerprint_data = {
        "user_agent": ua,
        "platform": platform,
        "screen": screen,
        "language": device_info.get("language", "") if device_info else "",
        "timezone": device_info.get("timezone", "") if device_info else "",
    }
    fingerprint_str = str(sorted(fingerprint_data.items()))
    fingerprint_hash = hashlib.md5(fingerprint_str.encode()).hexdigest()
    
    # Проверяем частоту использования этого отпечатка
    cache_key = device_cache._make_key("device", fingerprint_hash)
    usage_count = device_cache.get(cache_key) or 0
    device_cache.set(cache_key, usage_count + 1, ttl=3600)  # 1 час
    
    # Если отпечаток используется слишком часто - подозрительно
    if usage_count > 10:  # Более 10 использований за час
        return DeviceRuleResult(score_delta=15, fraud_flag="frequent_device_fingerprint")

    return DeviceRuleResult(score_delta=0, fraud_flag=None)
