import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import FraudCheck, AnomalyDetection
from .config import settings

class AnomalyDetector:
    def __init__(self):
        self.feature_weights = {
            'typing_speed': 0.3,
            'session_duration': 0.2,
            'mouse_moves': 0.2,
            'first_click_delay': 0.15,
            'device_fingerprint_frequency': 0.15
        }
    
    def extract_features(self, check_data: Dict[str, Any]) -> Dict[str, float]:
        """Извлекает признаки для ML модели."""
        features = {}
        
        # Нормализация typing speed (чем меньше, тем подозрительнее)
        typing_speed = check_data.get('typing_speed_ms_avg', 100)
        features['typing_speed'] = max(0, 1 - (typing_speed / 200))  # 0-1 scale
        
        # Нормализация session duration (слишком короткие подозрительны)
        session_duration = check_data.get('session_duration_ms', 10000)
        features['session_duration'] = min(1, session_duration / 30000)  # 0-1 scale
        
        # Нормализация mouse moves (отсутствие движений подозрительно)
        mouse_moves = check_data.get('mouse_moves_count', 10)
        features['mouse_moves'] = min(1, mouse_moves / 50)  # 0-1 scale
        
        # Нормализация first click delay (слишком быстрый подозрителен)
        first_click = check_data.get('first_click_delay_ms', 1000)
        features['first_click_delay'] = max(0, 1 - (first_click / 2000))  # 0-1 scale
        
        # Device fingerprint frequency (из кэша)
        device_freq = check_data.get('device_fingerprint_frequency', 1)
        features['device_fingerprint_frequency'] = min(1, device_freq / 10)  # 0-1 scale
        
        return features
    
    def calculate_anomaly_score(self, features: Dict[str, float]) -> float:
        """Вычисляет anomaly score на основе признаков."""
        weighted_score = 0
        total_weight = 0
        
        for feature, value in features.items():
            weight = self.feature_weights.get(feature, 0.1)
            weighted_score += value * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0
    
    def detect_anomalies(self, check_data: Dict[str, Any], threshold: float = 0.7) -> Tuple[float, bool, str]:
        """Определяет аномалии в данных проверки."""
        features = self.extract_features(check_data)
        anomaly_score = self.calculate_anomaly_score(features)
        
        is_anomaly = anomaly_score > threshold
        anomaly_type = "behavioral" if is_anomaly else "normal"
        
        return anomaly_score, is_anomaly, anomaly_type
    
    def get_historical_baseline(self, db: Session, days: int = 30) -> Dict[str, float]:
        """Получает исторические данные для baseline."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        checks = db.query(FraudCheck).filter(
            FraudCheck.created_at >= cutoff_date
        ).all()
        
        if not checks:
            return {}
        
        # Собираем статистики
        typing_speeds = [c.typing_speed_ms_avg for c in checks if c.typing_speed_ms_avg]
        session_durations = [c.session_duration_ms for c in checks if c.session_duration_ms]
        mouse_moves = [c.mouse_moves_count for c in checks if c.mouse_moves_count]
        
        baseline = {}
        if typing_speeds:
            baseline['typing_speed_mean'] = np.mean(typing_speeds)
            baseline['typing_speed_std'] = np.std(typing_speeds)
        
        if session_durations:
            baseline['session_duration_mean'] = np.mean(session_durations)
            baseline['session_duration_std'] = np.std(session_durations)
        
        if mouse_moves:
            baseline['mouse_moves_mean'] = np.mean(mouse_moves)
            baseline['mouse_moves_std'] = np.std(mouse_moves)
        
        return baseline

# Глобальный детектор аномалий
anomaly_detector = AnomalyDetector()
