from __future__ import annotations
from typing import Dict, Any, Optional
from pydantic import BaseModel
import httpx
from ..cache import geo_cache, bin_cache
from ..config import settings

# Простой мок BIN->country
BIN_MOCK = {
    "411111": "US",
    "400000": "US",
    "555555": "GB",
    "222222": "DE",
}


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
    if not ip:
        # Если не передали IP, попытка определить через ipapi ко внешнему IP сервера —
        # для MVP вернём None
        return None
    url = f"https://ipapi.co/{ip}/json/"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url)
            if r.status_code == 200:
                data = r.json()
                return data.get("country")
    except Exception:
        return None
    return None


def bin_country_lookup(bin6: Optional[str]) -> Optional[str]:
    if not bin6 or len(bin6) < 6:
        return None
    
    # Проверяем кэш
    cache_key = bin_cache._make_key("bin", bin6[:6])
    cached = bin_cache.get(cache_key)
    if cached is not None:
        return cached
    if not bin6 or len(bin6) < 6:
        return None
    country = BIN_MOCK.get(bin6[:6])
    if country:
        bin_cache.set(cache_key, country)
    return country


async def check_geo_and_bin(bin6: Optional[str], ip: Optional[str]) -> GeoRuleResult:
    ip_country = await get_ip_country(ip)
    bin_country = bin_country_lookup(bin6)

    if ip_country and bin_country and ip_country != bin_country:
        return GeoRuleResult(score_delta=settings.score_geo_mismatch, fraud_flag="geo_mismatch", details={"ip_country": ip_country, "bin_country": bin_country})

    return GeoRuleResult(score_delta=0, fraud_flag=None, details={"ip_country": ip_country, "bin_country": bin_country})
