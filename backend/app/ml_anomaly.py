"""
Machine Learning модуль для детекции аномалий в антифрод системе
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import json
import hashlib
from datetime import datetime, timedelta
from ..cache import device_cache
from ..config import settings
from pydantic import BaseModel


class MLAnomalyResult(BaseModel):
    score_delta: int
    fraud_flag: Optional[str] = None
    details: Dict[str, Any] | None = None


class AnomalyDetector:
    """Детектор аномалий на основе машинного обучения"""
    
    def __init__(self):
        self.feature_weights = {
            'typing_speed': 0.15,
            'mouse_movements': 0.20,
            'session_duration': 0.10,
            'first_click_time': 0.15,
            'device_fingerprint': 0.25,
            'geo_mismatch': 0.15
        }
        
        # Нормальные диапазоны для различных метрик
        self.normal_ranges = {
            'typing_speed': (50, 200),  # символов в минуту
            'mouse_movements': (10, 100),  # движений за сессию
            'session_duration': (30, 1800),  # секунды
            'first_click_time': (1, 30),  # секунды
        }
    
    def extract_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Извлекает признаки для ML модели"""
        features = {}
        
        # Скорость печати
        typing_speed = data.get('typing_speed', 0)
        features['typing_speed'] = float(typing_speed) if typing_speed else 0
        
        # Движения мыши
        mouse_movements = data.get('mouse_movements', 0)
        features['mouse_movements'] = float(mouse_movements) if mouse_movements else 0
        
        # Длительность сессии
        session_duration = data.get('session_duration', 0)
        features['session_duration'] = float(session_duration) if session_duration else 0
        
        # Время первого клика
        first_click_time = data.get('first_click_time', 0)
        features['first_click_time'] = float(first_click_time) if first_click_time else 0
        
        # Device fingerprint (уникальность)
        device_fingerprint = self._calculate_device_uniqueness(data)
        features['device_fingerprint'] = device_fingerprint
        
        # Geo mismatch (0 или 1)
        geo_mismatch = 1 if data.get('geo_mismatch', False) else 0
        features['geo_mismatch'] = geo_mismatch
        
        return features
    
    def _calculate_device_uniqueness(self, data: Dict[str, Any]) -> float:
        """Вычисляет уникальность устройства (0-1, где 1 = уникальное)"""
        device_info = data.get('deviceInfo', {})
        user_agent = data.get('userAgent', '')
        
        # Создаем fingerprint
        fingerprint_data = {
            'user_agent': user_agent.lower(),
            'platform': device_info.get('platform', ''),
            'screen': device_info.get('screen', {}),
            'language': device_info.get('language', ''),
            'timezone': device_info.get('timezone', ''),
        }
        
        fingerprint_str = str(sorted(fingerprint_data.items()))
        fingerprint_hash = hashlib.md5(fingerprint_str.encode()).hexdigest()
        
        # Проверяем частоту использования
        cache_key = device_cache._make_key("ml_device", fingerprint_hash)
        usage_count = device_cache.get(cache_key) or 0
        device_cache.set(cache_key, usage_count + 1, ttl=86400)  # 24 часа
        
        # Возвращаем обратную частоту (чем реже используется, тем уникальнее)
        return 1.0 / (1.0 + usage_count)
    
    def detect_anomalies(self, features: Dict[str, float]) -> List[Tuple[str, float, str]]:
        """Детектирует аномалии в признаках"""
        anomalies = []
        
        for feature_name, value in features.items():
            if feature_name in self.normal_ranges:
                min_val, max_val = self.normal_ranges[feature_name]
                
                # Проверяем выход за границы
                if value < min_val or value > max_val:
                    anomaly_score = self._calculate_anomaly_score(value, min_val, max_val)
                    anomaly_type = self._get_anomaly_type(feature_name, value, min_val, max_val)
                    anomalies.append((feature_name, anomaly_score, anomaly_type))
        
        return anomalies
    
    def _calculate_anomaly_score(self, value: float, min_val: float, max_val: float) -> float:
        """Вычисляет оценку аномальности (0-1)"""
        if value < min_val:
            return min(1.0, (min_val - value) / min_val)
        elif value > max_val:
            return min(1.0, (value - max_val) / max_val)
        return 0.0
    
    def _get_anomaly_type(self, feature_name: str, value: float, min_val: float, max_val: float) -> str:
        """Определяет тип аномалии"""
        if value < min_val:
            return f"low_{feature_name}"
        elif value > max_val:
            return f"high_{feature_name}"
        return f"unusual_{feature_name}"
    
    def calculate_ml_score(self, features: Dict[str, float], anomalies: List[Tuple[str, float, str]]) -> int:
        """Вычисляет ML score на основе признаков и аномалий"""
        base_score = 0
        
        # Базовый score на основе аномалий
        for feature_name, anomaly_score, anomaly_type in anomalies:
            weight = self.feature_weights.get(feature_name, 0.1)
            base_score += int(anomaly_score * 50 * weight)
        
        # Дополнительные проверки
        if features.get('device_fingerprint', 1) < 0.1:  # Очень часто используемое устройство
            base_score += 30
        
        if features.get('geo_mismatch', 0) == 1:  # Гео несоответствие
            base_score += 25
        
        # Проверка на бота по комбинации признаков
        if (features.get('typing_speed', 0) > 300 or  # Слишком быстрая печать
            features.get('mouse_movements', 0) < 5 or  # Слишком мало движений мыши
            features.get('first_click_time', 0) < 0.5):  # Слишком быстрый клик
            base_score += 40
        
        return min(base_score, 100)  # Ограничиваем максимальным score


def check_ml_anomalies(data: Dict[str, Any]) -> MLAnomalyResult:
    """Основная функция для проверки ML аномалий"""
    detector = AnomalyDetector()
    
    # Извлекаем признаки
    features = detector.extract_features(data)
    
    # Детектируем аномалии
    anomalies = detector.detect_anomalies(features)
    
    # Вычисляем ML score
    ml_score = detector.calculate_ml_score(features, anomalies)
    
    # Определяем fraud flag
    fraud_flag = None
    if ml_score > 70:
        fraud_flag = "ml_high_risk"
    elif ml_score > 40:
        fraud_flag = "ml_medium_risk"
    elif ml_score > 20:
        fraud_flag = "ml_low_risk"
    
    # Подготавливаем детали
    details = {
        'ml_score': ml_score,
        'features': features,
        'anomalies': [
            {
                'feature': anomaly[0],
                'score': anomaly[1],
                'type': anomaly[2]
            }
            for anomaly in anomalies
        ],
        'feature_weights': detector.feature_weights
    }
    
    return MLAnomalyResult(
        score_delta=ml_score,
        fraud_flag=fraud_flag,
        details=details
    )


class BehavioralAnalyzer:
    """Анализатор поведенческих паттернов"""
    
    def __init__(self):
        self.pattern_cache = {}
    
    def analyze_behavior(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализирует поведенческие паттерны"""
        analysis = {
            'human_like_score': 0,
            'bot_indicators': [],
            'suspicious_patterns': [],
            'risk_factors': []
        }
        
        # Анализ скорости печати
        typing_speed = data.get('typing_speed', 0)
        if typing_speed > 0:
            if 50 <= typing_speed <= 200:
                analysis['human_like_score'] += 20
            elif typing_speed < 10 or typing_speed > 400:
                analysis['bot_indicators'].append('unusual_typing_speed')
                analysis['risk_factors'].append('typing_speed')
        
        # Анализ движений мыши
        mouse_movements = data.get('mouse_movements', 0)
        if mouse_movements > 0:
            if 10 <= mouse_movements <= 100:
                analysis['human_like_score'] += 15
            elif mouse_movements < 3:
                analysis['bot_indicators'].append('minimal_mouse_movement')
                analysis['risk_factors'].append('mouse_movement')
        
        # Анализ времени сессии
        session_duration = data.get('session_duration', 0)
        if session_duration > 0:
            if 30 <= session_duration <= 1800:
                analysis['human_like_score'] += 10
            elif session_duration < 5:
                analysis['bot_indicators'].append('very_short_session')
                analysis['risk_factors'].append('session_duration')
        
        # Анализ времени первого клика
        first_click_time = data.get('first_click_time', 0)
        if first_click_time > 0:
            if 1 <= first_click_time <= 30:
                analysis['human_like_score'] += 15
            elif first_click_time < 0.5:
                analysis['bot_indicators'].append('instant_click')
                analysis['risk_factors'].append('first_click_time')
        
        # Анализ User-Agent
        user_agent = data.get('userAgent', '').lower()
        if any(keyword in user_agent for keyword in ['bot', 'crawler', 'spider', 'scraper']):
            analysis['bot_indicators'].append('bot_user_agent')
            analysis['risk_factors'].append('user_agent')
        
        # Анализ устройства
        device_info = data.get('deviceInfo', {})
        screen = device_info.get('screen', {})
        if screen.get('width', 0) == 0 or screen.get('height', 0) == 0:
            analysis['suspicious_patterns'].append('invalid_screen_resolution')
            analysis['risk_factors'].append('screen_resolution')
        
        return analysis


def analyze_behavioral_patterns(data: Dict[str, Any]) -> MLAnomalyResult:
    """Анализирует поведенческие паттерны пользователя"""
    analyzer = BehavioralAnalyzer()
    analysis = analyzer.analyze_behavior(data)
    
    # Вычисляем score на основе анализа
    base_score = 0
    
    # Штрафы за ботов
    base_score += len(analysis['bot_indicators']) * 15
    
    # Штрафы за подозрительные паттерны
    base_score += len(analysis['suspicious_patterns']) * 10
    
    # Штрафы за факторы риска
    base_score += len(analysis['risk_factors']) * 8
    
    # Бонус за человеческое поведение
    base_score -= min(analysis['human_like_score'], 50)
    
    # Ограничиваем score
    final_score = max(0, min(base_score, 100))
    
    # Определяем fraud flag
    fraud_flag = None
    if final_score > 60:
        fraud_flag = "behavioral_high_risk"
    elif final_score > 30:
        fraud_flag = "behavioral_medium_risk"
    elif final_score > 15:
        fraud_flag = "behavioral_low_risk"
    
    return MLAnomalyResult(
        score_delta=final_score,
        fraud_flag=fraud_flag,
        details={
            'behavioral_analysis': analysis,
            'final_score': final_score
        }
    )