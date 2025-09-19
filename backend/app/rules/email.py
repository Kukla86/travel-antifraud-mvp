from __future__ import annotations
from typing import Optional
from ..config import settings
from pydantic import BaseModel

TEMP_DOMAINS = {"mailinator.com", "yopmail.com", "tempmail.com", "10minutemail.com"}


class EmailRuleResult(BaseModel):
    score_delta: int
    fraud_flag: Optional[str] = None


def check_email_reputation(email: str) -> EmailRuleResult:
    # Простейшая проверка домена
    domain = email.split("@")[-1].lower().strip() if email and "@" in email else ""
    if domain in TEMP_DOMAINS:
        return EmailRuleResult(score_delta=settings.score_temp_email, fraud_flag="temporary_email")
    return EmailRuleResult(score_delta=0, fraud_flag=None)
