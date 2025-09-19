from __future__ import annotations
from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Float
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
from .db import Base


class FraudCheck(Base):
    __tablename__ = "fraud_checks"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    ip = Column(String(64), index=True, nullable=False)
    bin = Column(String(16), index=True, nullable=True)
    user_agent = Column(Text, nullable=True)

    ip_country = Column(String(8), index=True, nullable=True)
    bin_country = Column(String(8), index=True, nullable=True)

    timezone = Column(String(64), nullable=True)
    language = Column(String(32), nullable=True)

    # Метрики поведения/бота
    session_duration_ms = Column(Integer, nullable=True)
    typing_speed_ms_avg = Column(Integer, nullable=True)
    mouse_moves_count = Column(Integer, nullable=True)
    first_click_delay_ms = Column(Integer, nullable=True)

    device_info = Column(Text, nullable=True)  # JSON-строка

    risk_score = Column(Integer, nullable=False)
    fraud_flags = Column(Text, nullable=False)  # JSON-массив строк

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Индексы для производительности
    __table_args__ = (
        Index('idx_email_created', 'email', 'created_at'),
        Index('idx_ip_created', 'ip', 'created_at'),
        Index('idx_risk_score_created', 'risk_score', 'created_at'),
        Index('idx_fraud_flags', 'fraud_flags'),
    )


class BlacklistIP(Base):
    __tablename__ = "blacklist_ips"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String(64), unique=True, index=True, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="analyst")
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index('idx_user_action', 'user_id', 'action'),
        Index('idx_created_at', 'created_at'),
    )


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    model_type = Column(String(50), nullable=False)  # anomaly, clustering, etc.
    parameters = Column(JSON, nullable=True)
    accuracy = Column(Float, nullable=True)
    is_active = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AnomalyDetection(Base):
    __tablename__ = "anomaly_detections"

    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(Integer, nullable=False, index=True)
    anomaly_score = Column(Float, nullable=False)
    anomaly_type = Column(String(50), nullable=False)
    features = Column(JSON, nullable=True)
    is_anomaly = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_check_anomaly', 'check_id', 'is_anomaly'),
        Index('idx_anomaly_score', 'anomaly_score'),
    )
