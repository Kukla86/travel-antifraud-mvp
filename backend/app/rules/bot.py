from __future__ import annotations
from typing import Optional
from ..config import settings
from pydantic import BaseModel


class BotRuleResult(BaseModel):
    score_delta: int
    fraud_flag: Optional[str] = None


def check_bot_activity(session_duration_ms: Optional[int], mouse_moves_count: Optional[int], first_click_delay_ms: Optional[int], typing_speed_ms_avg: Optional[int]) -> BotRuleResult:
    # Простые эвристики: слишком быстрая сессия без движений мыши, либо экстремально быстрый клик
    if session_duration_ms is not None and mouse_moves_count is not None:
        if session_duration_ms < 3000 or mouse_moves_count == 0:
            return BotRuleResult(score_delta=settings.score_bot_activity, fraud_flag="bot_like_activity")
    if first_click_delay_ms is not None and first_click_delay_ms < 200:
        return BotRuleResult(score_delta=settings.score_bot_activity, fraud_flag="bot_like_activity")
    if typing_speed_ms_avg is not None and typing_speed_ms_avg < 40:
        return BotRuleResult(score_delta=settings.score_typing_too_fast, fraud_flag="autofill_or_bot")
    return BotRuleResult(score_delta=0, fraud_flag=None)
