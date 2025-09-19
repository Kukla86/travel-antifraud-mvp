#!/usr/bin/env python3
"""
Скрипт очистки старых логов из БД.
Запускать по cron: 0 2 * * * (каждый день в 2:00)
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Добавляем путь к приложению
sys.path.append(str(Path(__file__).parent))

from app.config import settings
from app.models import FraudCheck

def cleanup_old_logs():
    """Удаляет логи старше LOG_RETENTION_DAYS дней."""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    cutoff_date = datetime.utcnow() - timedelta(days=settings.log_retention_days)
    
    with SessionLocal() as db:
        # Подсчитываем сколько записей будет удалено
        count_query = text("SELECT COUNT(*) FROM fraud_checks WHERE created_at < :cutoff")
        count_result = db.execute(count_query, {"cutoff": cutoff_date})
        count = count_result.scalar()
        
        if count > 0:
            # Удаляем старые записи
            delete_query = text("DELETE FROM fraud_checks WHERE created_at < :cutoff")
            db.execute(delete_query, {"cutoff": cutoff_date})
            db.commit()
            print(f"Deleted {count} old log entries")
        else:
            print("No old entries to delete")

if __name__ == "__main__":
    cleanup_old_logs()
