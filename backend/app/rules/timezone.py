from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

# Грубая карта стран к основным таймзонам
COUNTRY_TIMEZONES = {
    "US": ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"],
    "GB": ["Europe/London"],
    "DE": ["Europe/Berlin"],
    "FR": ["Europe/Paris"],
    "IT": ["Europe/Rome"],
    "ES": ["Europe/Madrid"],
    "RU": ["Europe/Moscow"],
    "CN": ["Asia/Shanghai"],
    "JP": ["Asia/Tokyo"],
    "AU": ["Australia/Sydney", "Australia/Melbourne"],
    "CA": ["America/Toronto", "America/Vancouver"],
    "BR": ["America/Sao_Paulo"],
    "IN": ["Asia/Kolkata"],
    "MX": ["America/Mexico_City"],
}


class TimezoneRuleResult(BaseModel):
    score_delta: int
    fraud_flag: Optional[str] = None


def check_timezone_mismatch(ip_country: Optional[str], timezone: Optional[str]) -> TimezoneRuleResult:
    """Проверяет несоответствие IP-страны и таймзоны."""
    if not ip_country or not timezone:
        return TimezoneRuleResult(score_delta=0, fraud_flag=None)
    
    expected_zones = COUNTRY_TIMEZONES.get(ip_country, [])
    if not expected_zones:
        return TimezoneRuleResult(score_delta=0, fraud_flag=None)
    
    # Простая проверка: если таймзона не содержит ожидаемые зоны
    timezone_lower = timezone.lower()
    if not any(zone.lower() in timezone_lower for zone in expected_zones):
        return TimezoneRuleResult(score_delta=20, fraud_flag="timezone_mismatch")
    
    return TimezoneRuleResult(score_delta=0, fraud_flag=None)
