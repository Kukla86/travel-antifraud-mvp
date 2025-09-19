from __future__ import annotations
from typing import List, Tuple
from .config import settings


def aggregate_score_and_flags(parts: List[Tuple[int, str | None]]) -> tuple[int, list[str]]:
    # Суммируем score_delta и собираем флаги (уникальные)
    score = 0
    flags: list[str] = []
    for delta, flag in parts:
        score += max(0, int(delta))
        if flag and flag not in flags:
            flags.append(flag)
    # Клиппинг до 0..100
    score = max(0, min(100, score))
    return score, flags


def recommendation_from_score(score: int) -> str:
    if score >= settings.threshold_block:
        return "block"
    if score >= settings.threshold_review:
        return "review"
    return "allow"
