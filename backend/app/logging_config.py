import logging
import json
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Добавляем дополнительные поля если есть
        if hasattr(record, 'check_id'):
            log_entry['check_id'] = record.check_id
        if hasattr(record, 'ip'):
            log_entry['ip'] = record.ip
        if hasattr(record, 'email'):
            log_entry['email'] = record.email
        if hasattr(record, 'rule_name'):
            log_entry['rule_name'] = record.rule_name
        if hasattr(record, 'score_delta'):
            log_entry['score_delta'] = record.score_delta
        if hasattr(record, 'fraud_flag'):
            log_entry['fraud_flag'] = record.fraud_flag
            
        return json.dumps(log_entry)


def setup_logging():
    """Настраивает логирование в JSON формате."""
    # Основной логгер
    logger = logging.getLogger("antifraud")
    logger.setLevel(logging.INFO)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # Обработчик для файла
    file_handler = logging.FileHandler("antifraud.log")
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Логгер для правил
    rules_logger = logging.getLogger("antifraud.rules")
    rules_logger.setLevel(logging.DEBUG)
    
    return logger, rules_logger


# Глобальные логгеры
main_logger, rules_logger = setup_logging()


def log_check_start(check_id: int, email: str, ip: str):
    """Логирует начало проверки."""
    main_logger.info("Check started", extra={
        "check_id": check_id,
        "email": email,
        "ip": ip
    })


def log_rule_result(rule_name: str, score_delta: int, fraud_flag: str = None, details: Dict[str, Any] = None):
    """Логирует результат правила."""
    rules_logger.info(f"Rule {rule_name} executed", extra={
        "rule_name": rule_name,
        "score_delta": score_delta,
        "fraud_flag": fraud_flag,
        "details": details or {}
    })


def log_check_complete(check_id: int, risk_score: int, fraud_flags: list, recommendation: str):
    """Логирует завершение проверки."""
    main_logger.info("Check completed", extra={
        "check_id": check_id,
        "risk_score": risk_score,
        "fraud_flags": fraud_flags,
        "recommendation": recommendation
    })
