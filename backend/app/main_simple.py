from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from datetime import datetime, timedelta

from .config import settings
from .db import Base, engine, get_db
from .models import FraudCheck, BlacklistIP
from .schemas import CheckRequest, CheckResponse
from .rules.geo import check_geo_and_bin
from .rules.email import check_email_reputation
from .rules.velocity import check_velocity
from .rules.bot import check_bot_activity
from .rules.device import check_device
from .rules.blacklist import check_blacklist_ip
from .rules.timezone import check_timezone_mismatch
from .risk_score import aggregate_score_and_flags, recommendation_from_score
from .logging_config import log_check_start, log_rule_result, log_check_complete
from .rate_limiter import rate_limiter
from pydantic import BaseModel

app = FastAPI(title="Travel Antifraud MVP - Simple Version")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Сидирование blacklist IP из .env при старте
seed_ips = [ip.strip() for ip in (settings.seed_blacklist_ips or "").split(",") if ip.strip()]
if seed_ips:
    with next(get_db()) as db:
        existing = {row.ip for row in db.query(BlacklistIP).all()}
        for ip in seed_ips:
            if ip not in existing:
                db.add(BlacklistIP(ip=ip))
        db.commit()

class BlacklistRequest(BaseModel):
    ip: str

@app.post("/api/check", response_model=CheckResponse)
async def api_check(
    payload: CheckRequest, 
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
) -> CheckResponse:
    # Проверка API ключа
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Rate limiting (простая версия)
    if not rate_limiter.is_allowed(f"ip:{payload.ip or 'unknown'}", settings.rate_limit_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for IP")
    
    if payload.email and not rate_limiter.is_allowed(f"email:{payload.email}", settings.rate_limit_email):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for email")
    
    # Логируем начало проверки
    log_check_start(0, payload.email, payload.ip or "unknown")
    
    # Запуск правил
    geo_res = await check_geo_and_bin(payload.bin, payload.ip)
    log_rule_result("geo", geo_res.score_delta, geo_res.fraud_flag, geo_res.details)
    
    timezone_res = check_timezone_mismatch(geo_res.details.get("ip_country") if geo_res.details else None, payload.timezone)
    log_rule_result("timezone", timezone_res.score_delta, timezone_res.fraud_flag)
    
    email_res = check_email_reputation(payload.email)
    log_rule_result("email", email_res.score_delta, email_res.fraud_flag)
    
    velocity_res = check_velocity(db, payload.email, payload.ip or "")
    log_rule_result("velocity", velocity_res.score_delta, velocity_res.fraud_flag)
    
    bot_res = check_bot_activity(payload.session_duration_ms, payload.mouse_moves_count, payload.first_click_delay_ms, payload.typing_speed_ms_avg)
    log_rule_result("bot", bot_res.score_delta, bot_res.fraud_flag)
    
    device_res = check_device(payload.device_info, payload.user_agent)
    log_rule_result("device", device_res.score_delta, device_res.fraud_flag)
    
    blacklist_res = check_blacklist_ip(db, payload.ip)
    log_rule_result("blacklist", blacklist_res.score_delta, blacklist_res.fraud_flag)
    
    parts = [
        (geo_res.score_delta, geo_res.fraud_flag),
        (timezone_res.score_delta, timezone_res.fraud_flag),
        (email_res.score_delta, email_res.fraud_flag),
        (velocity_res.score_delta, velocity_res.fraud_flag),
        (bot_res.score_delta, bot_res.fraud_flag),
        (device_res.score_delta, device_res.fraud_flag),
        (blacklist_res.score_delta, blacklist_res.fraud_flag),
    ]

    score, flags = aggregate_score_and_flags(parts)
    rec = recommendation_from_score(score)

    # Сохраняем лог
    log = FraudCheck(
        email=payload.email,
        ip=payload.ip or "",
        bin=(payload.bin or "")[:16],
        user_agent=payload.user_agent or "",
        ip_country=geo_res.details.get("ip_country") if geo_res.details else None,
        bin_country=geo_res.details.get("bin_country") if geo_res.details else None,
        timezone=payload.timezone,
        language=payload.language,
        session_duration_ms=payload.session_duration_ms,
        typing_speed_ms_avg=payload.typing_speed_ms_avg,
        mouse_moves_count=payload.mouse_moves_count,
        first_click_delay_ms=payload.first_click_delay_ms,
        device_info=json.dumps(payload.device_info or {}),
        risk_score=score,
        fraud_flags=json.dumps(flags),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Логируем завершение проверки
    log_check_complete(log.id, score, flags, rec)

    return CheckResponse(risk_score=score, fraud_flags=flags, recommendation=rec, check_id=log.id)

@app.get("/api/checks")
def list_checks(db: Session = Depends(get_db)):
    rows = db.query(FraudCheck).order_by(FraudCheck.id.desc()).limit(200).all()
    result: list[dict[str, Any]] = []
    for r in rows:
        result.append({
            "id": r.id,
            "email": r.email,
            "ip": r.ip,
            "bin": r.bin,
            "risk_score": r.risk_score,
            "fraud_flags": json.loads(r.fraud_flags or "[]"),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return result

@app.get("/api/checks/{check_id}")
def get_check(check_id: int, db: Session = Depends(get_db)):
    r = db.query(FraudCheck).filter(FraudCheck.id == check_id).first()
    if not r:
        return {"error": "not_found"}
    return {
        "id": r.id,
        "email": r.email,
        "ip": r.ip,
        "bin": r.bin,
        "user_agent": r.user_agent,
        "ip_country": r.ip_country,
        "bin_country": r.bin_country,
        "timezone": r.timezone,
        "language": r.language,
        "session_duration_ms": r.session_duration_ms,
        "typing_speed_ms_avg": r.typing_speed_ms_avg,
        "mouse_moves_count": r.mouse_moves_count,
        "first_click_delay_ms": r.first_click_delay_ms,
        "device_info": json.loads(r.device_info or "{}"),
        "risk_score": r.risk_score,
        "fraud_flags": json.loads(r.fraud_flags or "[]"),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }

@app.post("/api/blacklist")
def add_to_blacklist(
    payload: BlacklistRequest,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Проверяем, есть ли уже такой IP
    existing = db.query(BlacklistIP).filter(BlacklistIP.ip == payload.ip).first()
    if existing:
        return {"message": "IP already in blacklist"}
    
    # Добавляем в blacklist
    blacklist_entry = BlacklistIP(ip=payload.ip)
    db.add(blacklist_entry)
    db.commit()
    
    return {"message": "IP added to blacklist", "ip": payload.ip}

@app.get("/api/blacklist")
def list_blacklist(
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    ips = db.query(BlacklistIP).all()
    return [{"id": ip.id, "ip": ip.ip} for ip in ips]

@app.delete("/api/blacklist/{ip_id}")
def remove_from_blacklist(
    ip_id: int,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    ip_entry = db.query(BlacklistIP).filter(BlacklistIP.id == ip_id).first()
    if not ip_entry:
        raise HTTPException(status_code=404, detail="IP not found in blacklist")
    
    db.delete(ip_entry)
    db.commit()
    
    return {"message": "IP removed from blacklist"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/metrics")
def get_metrics():
    # Простые метрики
    with next(get_db()) as db:
        total_checks = db.query(FraudCheck).count()
        high_risk = db.query(FraudCheck).filter(FraudCheck.risk_score >= settings.threshold_review).count()
        blacklisted_ips = db.query(BlacklistIP).count()
    
    return {
        "total_checks": total_checks,
        "high_risk_checks": high_risk,
        "blacklisted_ips": blacklisted_ips,
    }

@app.get("/")
def root():
    return {"status": "ok", "version": "simple"}
