from __future__ import annotations
from typing import Dict, Any, Optional
from pydantic import BaseModel
import httpx
from ..cache import geo_cache, bin_cache
from ..config import settings

# Простой мок BIN->country (fallback)
BIN_MOCK = {
    "411111": "US",
    "400000": "US",
    "555555": "GB",
    "222222": "DE",
}

# Реальные BIN API endpoints
BIN_API_ENDPOINTS = [
    "https://lookup.binlist.net/",  # Основной API
    "https://binlist.net/api/v1/",  # Альтернативный
]


class GeoRuleResult(BaseModel):
    score_delta: int
    fraud_flag: Optional[str] = None
    details: Dict[str, Any] | None = None


async def get_ip_country(ip: Optional[str]) -> Optional[str]:
    if not ip:
        return None
    
    # Проверяем кэш
    cache_key = geo_cache._make_key("geo", ip)
    cached = geo_cache.get(cache_key)
    if cached is not None:
        return cached
    
    # Список API для геолокации
    geo_apis = [
        f"https://ipapi.co/{ip}/json/",
        f"https://ip-api.com/json/{ip}",
        f"https://ipinfo.io/{ip}/json",
    ]
    
    for url in geo_apis:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    country = None
                    
                    # Разные API возвращают данные в разных форматах
                    if "ipapi.co" in url:
                        country = data.get("country_code")
                    elif "ip-api.com" in url:
                        country = data.get("countryCode")
                    elif "ipinfo.io" in url:
                        country = data.get("country")
                    
                    if country:
                        geo_cache.set(cache_key, country, ttl=86400)  # 24 часа
                        return country
        except Exception:
            continue
    
    return None


async def bin_country_lookup(bin6: Optional[str]) -> Optional[str]:
    if not bin6 or len(bin6) < 6:
        return None
    
    # Проверяем кэш
    cache_key = bin_cache._make_key("bin", bin6[:6])
    cached = bin_cache.get(cache_key)
    if cached is not None:
        return cached
    
    # Пробуем реальные API
    for api_url in BIN_API_ENDPOINTS:
        try:
            url = f"{api_url}{bin6[:6]}"
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    country = data.get("country", {}).get("alpha2")
                    if country:
                        bin_cache.set(cache_key, country, ttl=86400)  # 24 часа
                        return country
        except Exception:
            continue
    
    # Fallback на мок данные
    country = BIN_MOCK.get(bin6[:6])
    if country:
        bin_cache.set(cache_key, country, ttl=3600)  # 1 час для мок данных
    return country


async def check_geo_and_bin(bin6: Optional[str], ip: Optional[str]) -> GeoRuleResult:
    ip_country = await get_ip_country(ip)
    bin_country = await bin_country_lookup(bin6)

    if ip_country and bin_country and ip_country != bin_country:
        return GeoRuleResult(score_delta=settings.score_geo_mismatch, fraud_flag="geo_mismatch", details={"ip_country": ip_country, "bin_country": bin_country})

    return GeoRuleResult(score_delta=0, fraud_flag=None, details={"ip_country": ip_country, "bin_country": bin_country})
