from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException, Header, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

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
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("antifraud")

app = FastAPI(title="Travel Antifraud MVP - Working Version")

# CORS - исправленная версия
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все origins для демо
    allow_credentials=False,  # Отключаем credentials для file://
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Простой rate limiter в памяти
class SimpleRateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str, limit: int) -> bool:
        now = datetime.now()
        # Очищаем старые запросы (старше 1 минуты)
        self.requests[key] = [req_time for req_time in self.requests[key] 
                             if (now - req_time).seconds < 60]
        
        # Проверяем лимит
        if len(self.requests[key]) >= limit:
            return False
        
        # Добавляем текущий запрос
        self.requests[key].append(now)
        return True

rate_limiter = SimpleRateLimiter()

# WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Простые функции логирования
def log_check_start(check_id: int, email: str, ip: str):
    logger.info(f"Check started - ID: {check_id}, IP: {ip}, Email: {email}")

def log_rule_result(rule_name: str, score_delta: int, fraud_flag: Optional[str], details: Optional[Dict] = None):
    logger.info(f"Rule {rule_name} executed - Score: {score_delta}, Flag: {fraud_flag}")

def log_check_complete(check_id: int, score: int, flags: List[str], recommendation: str):
    logger.info(f"Check completed - ID: {check_id}, Score: {score}, Recommendation: {recommendation}")

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

class LoginRequest(BaseModel):
    username: str
    password: str

# Обработка OPTIONS запросов для CORS
@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    return {"message": "OK"}

@app.post("/api/check", response_model=CheckResponse)
async def api_check(
    payload: CheckRequest, 
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
) -> CheckResponse:
    # Проверка API ключа
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Rate limiting
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

    # Отправляем уведомление через WebSocket
    if score >= settings.threshold_review:
        await manager.broadcast(json.dumps({
            "type": "high_risk_alert",
            "check_id": log.id,
            "email": payload.email,
            "score": score,
            "flags": flags
        }))

    return CheckResponse(risk_score=score, fraud_flags=flags, recommendation=rec, check_id=log.id)

@app.get("/api/checks")
def list_checks(
    skip: int = 0, 
    limit: int = 100,
    email_filter: Optional[str] = None,
    ip_filter: Optional[str] = None,
    risk_min: Optional[int] = None,
    risk_max: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(FraudCheck)
    
    if email_filter:
        query = query.filter(FraudCheck.email.contains(email_filter))
    if ip_filter:
        query = query.filter(FraudCheck.ip.contains(ip_filter))
    if risk_min is not None:
        query = query.filter(FraudCheck.risk_score >= risk_min)
    if risk_max is not None:
        query = query.filter(FraudCheck.risk_score <= risk_max)
    
    rows = query.order_by(FraudCheck.id.desc()).offset(skip).limit(limit).all()
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
        raise HTTPException(status_code=404, detail="Check not found")
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

# Analytics endpoints
@app.get("/api/analytics/risk-distribution")
def get_risk_distribution(db: Session = Depends(get_db)):
    checks = db.query(FraudCheck).all()
    distribution = {
        "low": len([c for c in checks if c.risk_score < 30]),
        "medium": len([c for c in checks if 30 <= c.risk_score < 70]),
        "high": len([c for c in checks if c.risk_score >= 70])
    }
    return distribution

@app.get("/api/analytics/top-fraud-flags")
def get_top_fraud_flags(db: Session = Depends(get_db)):
    checks = db.query(FraudCheck).all()
    flag_counts = defaultdict(int)
    
    for check in checks:
        flags = json.loads(check.fraud_flags or "[]")
        for flag in flags:
            flag_counts[flag] += 1
    
    return dict(sorted(flag_counts.items(), key=lambda x: x[1], reverse=True)[:10])

@app.get("/api/analytics/suspicious-ips")
def get_suspicious_ips(db: Session = Depends(get_db)):
    # IP с высоким риском
    high_risk_ips = db.query(FraudCheck).filter(FraudCheck.risk_score >= 70).all()
    ip_counts = defaultdict(int)
    
    for check in high_risk_ips:
        ip_counts[check.ip] += 1
    
    return dict(sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10])

@app.get("/api/analytics/hourly-metrics")
def get_hourly_metrics(db: Session = Depends(get_db)):
    checks = db.query(FraudCheck).all()
    hourly = defaultdict(int)
    
    for check in checks:
        if check.created_at:
            hour = check.created_at.hour
            hourly[hour] += 1
    
    return dict(hourly)

@app.get("/api/analytics/rule-performance")
def get_rule_performance(db: Session = Depends(get_db)):
    checks = db.query(FraudCheck).all()
    rule_stats = defaultdict(lambda: {"total": 0, "flagged": 0})
    
    for check in checks:
        flags = json.loads(check.fraud_flags or "[]")
        for flag in flags:
            rule_stats[flag]["total"] += 1
            rule_stats[flag]["flagged"] += 1
    
    return {rule: {
        "total_checks": stats["total"],
        "flagged": stats["flagged"],
        "flag_rate": stats["flagged"] / max(stats["total"], 1) * 100
    } for rule, stats in rule_stats.items()}

# Auth endpoints (простая версия)
@app.post("/api/auth/login")
def login(payload: LoginRequest):
    # Простая аутентификация для демо
    if payload.username == "admin" and payload.password == "admin123":
        return {"access_token": "demo_token", "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/auth/me")
def get_current_user():
    return {"username": "admin", "role": "admin"}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Эхо-ответ
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    total_checks = db.query(FraudCheck).count()
    high_risk = db.query(FraudCheck).filter(FraudCheck.risk_score >= settings.threshold_review).count()
    blacklisted_ips = db.query(BlacklistIP).count()
    
    return {
        "total_checks": total_checks,
        "high_risk_checks": high_risk,
        "blacklisted_ips": blacklisted_ips,
        "active_connections": len(manager.active_connections)
    }

@app.get("/")
def root():
    return {"status": "ok", "version": "working", "endpoints": [
        "/api/check", "/api/checks", "/api/blacklist", 
        "/api/analytics/*", "/api/auth/*", "/ws", "/health", "/metrics"
    ]}
