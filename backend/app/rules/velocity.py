from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models import FraudCheck
from ..config import settings
from pydantic import BaseModel
from datetime import datetime, timedelta


class VelocityRuleResult(BaseModel):
    score_delta: int
    fraud_flag: Optional[str] = None


def check_velocity(db: Session, email: str, ip: str) -> VelocityRuleResult:
    # Кол-во попыток за последние 5 минут по email и ip
    since = datetime.utcnow() - timedelta(minutes=5)
    # Приведение created_at (timezone-aware) к naive UTC может отличаться, для MVP используем >= since по серверному времени
    q = select(func.count()).select_from(FraudCheck).where(
        FraudCheck.email == email,
    ).where(FraudCheck.created_at >= since)
    attempts_email = db.execute(q).scalar() or 0

    q2 = select(func.count()).select_from(FraudCheck).where(
        FraudCheck.ip == ip,
    ).where(FraudCheck.created_at >= since)
    attempts_ip = db.execute(q2).scalar() or 0

    if attempts_email > 3 or attempts_ip > 3:
        return VelocityRuleResult(score_delta=settings.score_velocity, fraud_flag="too_many_attempts")
    return VelocityRuleResult(score_delta=0, fraud_flag=None)
