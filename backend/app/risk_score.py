from __future__ import annotations
from typing import List, Tuple, Dict, Any
from .config import settings
from .ml_anomaly import check_ml_anomalies, analyze_behavioral_patterns


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


def calculate_ml_enhanced_score(data: Dict[str, Any], rule_results: List[Tuple[int, str | None]]) -> Tuple[int, List[str], Dict[str, Any]]:
    """Расширенный расчет score с ML анализом"""
    
    # Базовый score от правил
    base_score, base_flags = aggregate_score_and_flags(rule_results)
    
    # ML анализ аномалий
    ml_anomaly_result = check_ml_anomalies(data)
    ml_anomaly_score = ml_anomaly_result.score_delta
    ml_anomaly_flag = ml_anomaly_result.fraud_flag
    
    # Поведенческий анализ
    behavioral_result = analyze_behavioral_patterns(data)
    behavioral_score = behavioral_result.score_delta
    behavioral_flag = behavioral_result.fraud_flag
    
    # Комбинируем scores
    total_score = base_score + ml_anomaly_score + behavioral_score
    total_score = max(0, min(100, total_score))  # Ограничиваем 0-100
    
    # Собираем все флаги
    all_flags = base_flags.copy()
    if ml_anomaly_flag:
        all_flags.append(ml_anomaly_flag)
    if behavioral_flag:
        all_flags.append(behavioral_flag)
    
    # Подготавливаем детали
    details = {
        'base_score': base_score,
        'ml_anomaly_score': ml_anomaly_score,
        'behavioral_score': behavioral_score,
        'total_score': total_score,
        'ml_details': ml_anomaly_result.details,
        'behavioral_details': behavioral_result.details
    }
    
    return total_score, all_flags, details
