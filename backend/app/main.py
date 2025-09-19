from __future__ import annotations
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from .config import settings
from .db import Base, engine, get_db
from .models import FraudCheck, BlacklistIP, User, AuditLog, MLModel, AnomalyDetection
from .cache import geo_cache, bin_cache, device_cache
from .logging_config import log_check_start, log_rule_result, log_check_complete
from .redis_client import redis_client
from .auth import create_access_token, verify_token, USERS
from .websocket_manager import websocket_manager
from .rate_limiter_redis import redis_rate_limiter
from .ml_anomaly import anomaly_detector
from .analytics import analytics_engine
from .models import User, AuditLog, MLModel, AnomalyDetection
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import asyncio
from .schemas import CheckRequest, CheckResponse
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class MetricsResponse(BaseModel):
    total_checks: int
    high_risk_checks: int
    blacklisted_ips: int
    cache_size: dict
    risk_distribution: dict
    top_fraud_flags: list
    suspicious_ips: list
    hourly_metrics: list
    rule_performance: dict

class BlacklistRequest(BaseModel):
    ip: str
from .rules.geo import check_geo_and_bin
from .rules.timezone import check_timezone_mismatch
from .rules.email import check_email_reputation
from .rules.velocity import check_velocity
from .rules.bot import check_bot_activity
from .rules.device import check_device
from .rules.blacklist import check_blacklist_ip
from .risk_score import aggregate_score_and_flags, recommendation_from_score
from .rate_limiter import rate_limiter
from fastapi import HTTPException, Header
from typing import Optional

app = FastAPI(title="Travel Antifraud MVP")

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

# Инициализация Redis
@app.on_event("startup")
async def startup_event():
    await redis_client.connect()
    print("Redis connected")

@app.on_event("shutdown")
async def shutdown_event():
    await redis_client.disconnect()
    print("Redis disconnected")

# JWT Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

# Audit logging
def log_audit_action(db: Session, user_id: int, action: str, resource_type: str = None, resource_id: str = None, details: dict = None, ip_address: str = None, user_agent: str = None):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit_log)
    db.commit()


# Сидирование blacklist IP из .env при старте
# Очистка кэшей при старте
seed_ips = [ip.strip() for ip in (settings.seed_blacklist_ips or "").split(",") if ip.strip()]
if seed_ips:
    with next(get_db()) as db:
        existing = {row.ip for row in db.query(BlacklistIP).all()}
        for ip in seed_ips:
            if ip not in existing:
                db.add(BlacklistIP(ip=ip))
        db.commit()

# Очистка кэшей при старте
geo_cache.cleanup()
bin_cache.cleanup()
device_cache.cleanup()


@app.post("/api/check", response_model=CheckResponse)
async def api_check(
    payload: CheckRequest, 
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
) -> CheckResponse:
    # Проверка API ключа
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Redis rate limiting
    if not await redis_rate_limiter.is_allowed(f"ip:{payload.ip or 'unknown'}", settings.rate_limit_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for IP")
    
    if payload.email and not await redis_rate_limiter.is_allowed(f"email:{payload.email}", settings.rate_limit_email):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for email")
    
    # Логируем начало проверки
    log_check_start(0, payload.email, payload.ip or "unknown")  # check_id будет обновлён после сохранения
    
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

    # ML Anomaly Detection
    check_data = {
        "typing_speed_ms_avg": payload.typing_speed_ms_avg,
        "session_duration_ms": payload.session_duration_ms,
        "mouse_moves_count": payload.mouse_moves_count,
        "first_click_delay_ms": payload.first_click_delay_ms,
        "device_fingerprint_frequency": 1  # TODO: Get from cache
    }
    
    anomaly_score, is_anomaly, anomaly_type = anomaly_detector.detect_anomalies(check_data)
    
    # Сохраняем anomaly detection результат
    anomaly_record = AnomalyDetection(
        check_id=log.id,
        anomaly_score=anomaly_score,
        anomaly_type=anomaly_type,
        features=check_data,
        is_anomaly=1 if is_anomaly else 0
    )
    db.add(anomaly_record)
    db.commit()
    
    # WebSocket broadcast для high-risk транзакций
    if score >= settings.threshold_review:
        await websocket_manager.broadcast_fraud_alert({
            "check_id": log.id,
            "email": payload.email,
            "ip": payload.ip,
            "risk_score": score,
            "fraud_flags": flags,
            "recommendation": rec,
            "anomaly_score": anomaly_score
        })
    
    # Логируем завершение проверки
    log_check_complete(log.id, score, flags, rec)

    return CheckResponse(risk_score=score, fraud_flags=flags, recommendation=rec, check_id=log.id)


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


# Authentication endpoints
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user_data = USERS.get(login_data.username)
    if not user_data or not verify_password(login_data.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": login_data.username, "role": user_data["role"]})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={"username": login_data.username, "role": user_data["role"]}
    )


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    await websocket_manager.connect(websocket, token)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
            await websocket_manager.send_personal_message({"type": "ping"}, websocket)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


# Advanced Analytics endpoints
@app.get("/api/analytics/risk-distribution")
async def get_risk_distribution(days: int = 7, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return analytics_engine.get_risk_distribution(db, days)

@app.get("/api/analytics/top-fraud-flags")
async def get_top_fraud_flags(days: int = 7, limit: int = 10, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return analytics_engine.get_top_fraud_flags(db, days, limit)

@app.get("/api/analytics/suspicious-ips")
async def get_suspicious_ips(days: int = 7, limit: int = 10, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return analytics_engine.get_suspicious_ips(db, days, limit)

@app.get("/api/analytics/hourly-metrics")
async def get_hourly_metrics(days: int = 7, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return analytics_engine.get_hourly_metrics(db, days)

@app.get("/api/analytics/rule-performance")
async def get_rule_performance(days: int = 7, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return analytics_engine.get_rule_performance(db, days)


# Enhanced Metrics endpoint
@app.get("/api/metrics", response_model=MetricsResponse)
async def get_enhanced_metrics(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Basic metrics
    total_checks = db.query(FraudCheck).count()
    high_risk_checks = db.query(FraudCheck).filter(FraudCheck.risk_score >= settings.threshold_review).count()
    blacklisted_ips = db.query(BlacklistIP).count()
    
    # Cache sizes
    cache_size = {
        "geo": len(geo_cache._cache),
        "bin": len(bin_cache._cache),
        "device": len(device_cache._cache)
    }
    
    # Analytics
    risk_distribution = analytics_engine.get_risk_distribution(db, 7)
    top_fraud_flags = analytics_engine.get_top_fraud_flags(db, 7, 5)
    suspicious_ips = analytics_engine.get_suspicious_ips(db, 7, 5)
    hourly_metrics = analytics_engine.get_hourly_metrics(db, 7)
    rule_performance = analytics_engine.get_rule_performance(db, 7)
    
    return MetricsResponse(
        total_checks=total_checks,
        high_risk_checks=high_risk_checks,
        blacklisted_ips=blacklisted_ips,
        cache_size=cache_size,
        risk_distribution=risk_distribution,
        top_fraud_flags=top_fraud_flags,
        suspicious_ips=suspicious_ips,
        hourly_metrics=hourly_metrics,
        rule_performance=rule_performance
    )


# ML endpoints
@app.get("/api/ml/anomalies")
async def get_anomalies(days: int = 7, limit: int = 100, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    anomalies = db.query(AnomalyDetection).join(FraudCheck).filter(
        FraudCheck.created_at >= cutoff_date,
        AnomalyDetection.is_anomaly == 1
    ).order_by(desc(AnomalyDetection.anomaly_score)).limit(limit).all()
    
    return [
        {
            "check_id": anomaly.check_id,
            "anomaly_score": anomaly.anomaly_score,
            "anomaly_type": anomaly.anomaly_type,
            "features": anomaly.features,
            "created_at": anomaly.created_at.isoformat()
        }
        for anomaly in anomalies
    ]

@app.post("/api/ml/retrain")
async def retrain_model(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Простая retrain логика (в реальности нужен более сложный ML pipeline)
    baseline = anomaly_detector.get_historical_baseline(db, 30)
    
    # Сохраняем новую модель
    model = MLModel(
        name="anomaly_detector",
        version="1.1.0",
        model_type="anomaly",
        parameters=baseline,
        accuracy=0.85,  # Mock accuracy
        is_active=1
    )
    db.add(model)
    db.commit()
    
    return {"message": "Model retrained successfully", "baseline": baseline}


# Audit log endpoint
@app.get("/api/audit-logs")
async def get_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]


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
        "cache_size": {
            "geo": len(geo_cache._cache),
            "bin": len(bin_cache._cache),
            "device": len(device_cache._cache)
        }
    }


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


@app.get("/")
def root():
    return {"status": "ok"}
