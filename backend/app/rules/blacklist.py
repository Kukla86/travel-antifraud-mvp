from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import BlacklistIP
from ..config import settings
from pydantic import BaseModel


class BlacklistRuleResult(BaseModel):
    score_delta: int
    fraud_flag: Optional[str] = None


def check_blacklist_ip(db: Session, ip: Optional[str]) -> BlacklistRuleResult:
    if not ip:
        return BlacklistRuleResult(score_delta=0, fraud_flag=None)
    q = select(BlacklistIP).where(BlacklistIP.ip == ip)
    row = db.execute(q).scalar_one_or_none()
    if row is not None:
        return BlacklistRuleResult(score_delta=settings.score_ip_blacklisted, fraud_flag="ip_blacklisted")
    return BlacklistRuleResult(score_delta=0, fraud_flag=None)
