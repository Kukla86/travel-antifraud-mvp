from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class CheckRequest(BaseModel):
    email: str
    bin: Optional[str] = Field(default=None, description="First 6 digits")
    user_agent: Optional[str] = None
    ip: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

    # Метрики поведения
    session_duration_ms: Optional[int] = None
    typing_speed_ms_avg: Optional[int] = None
    mouse_moves_count: Optional[int] = None
    first_click_delay_ms: Optional[int] = None

    # Девайс
    device_info: Optional[Dict[str, Any]] = None


class RuleResult(BaseModel):
    score_delta: int
    fraud_flag: Optional[str] = None  # None если правило не сработало
    details: Optional[Dict[str, Any]] = None


class CheckResponse(BaseModel):
    risk_score: int
    fraud_flags: List[str]
    recommendation: str
    check_id: Optional[int] = None
