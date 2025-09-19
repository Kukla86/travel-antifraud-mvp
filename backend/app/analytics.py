from typing import Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from .models import FraudCheck, BlacklistIP

class AnalyticsEngine:
    def __init__(self):
        pass
    
    def get_risk_distribution(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """Распределение risk scores за период."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Группировка по диапазонам risk score
        low_risk = db.query(FraudCheck).filter(
            FraudCheck.created_at >= cutoff_date,
            FraudCheck.risk_score < 50
        ).count()
        
        medium_risk = db.query(FraudCheck).filter(
            FraudCheck.created_at >= cutoff_date,
            FraudCheck.risk_score >= 50,
            FraudCheck.risk_score < 80
        ).count()
        
        high_risk = db.query(FraudCheck).filter(
            FraudCheck.created_at >= cutoff_date,
            FraudCheck.risk_score >= 80
        ).count()
        
        total = low_risk + medium_risk + high_risk
        
        return {
            "low_risk": low_risk,
            "medium_risk": medium_risk,
            "high_risk": high_risk,
            "total": total,
            "percentages": {
                "low_risk": (low_risk / total * 100) if total > 0 else 0,
                "medium_risk": (medium_risk / total * 100) if total > 0 else 0,
                "high_risk": (high_risk / total * 100) if total > 0 else 0
            }
        }
    
    def get_top_fraud_flags(self, db: Session, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Топ флагов мошенничества."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Простой подсчёт флагов (в реальности нужен более сложный парсинг JSON)
        checks = db.query(FraudCheck).filter(
            FraudCheck.created_at >= cutoff_date,
            FraudCheck.fraud_flags.isnot(None)
        ).all()
        
        flag_counts = {}
        for check in checks:
            try:
                import json
                flags = json.loads(check.fraud_flags)
                for flag in flags:
                    flag_counts[flag] = flag_counts.get(flag, 0) + 1
            except:
                continue
        
        return [
            {"flag": flag, "count": count}
            for flag, count in sorted(flag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        ]
    
    def get_suspicious_ips(self, db: Session, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Топ подозрительных IP адресов."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        ip_stats = db.query(
            FraudCheck.ip,
            func.count(FraudCheck.id).label('check_count'),
            func.avg(FraudCheck.risk_score).label('avg_risk_score'),
            func.max(FraudCheck.created_at).label('last_seen')
        ).filter(
            FraudCheck.created_at >= cutoff_date,
            FraudCheck.ip.isnot(None)
        ).group_by(FraudCheck.ip).order_by(desc('avg_risk_score')).limit(limit).all()
        
        return [
            {
                "ip": stat.ip,
                "check_count": stat.check_count,
                "avg_risk_score": round(stat.avg_risk_score, 2),
                "last_seen": stat.last_seen.isoformat() if stat.last_seen else None
            }
            for stat in ip_stats
        ]
    
    def get_hourly_metrics(self, db: Session, days: int = 7) -> List[Dict[str, Any]]:
        """Метрики по часам."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        hourly_stats = db.query(
            func.strftime('%H', FraudCheck.created_at).label('hour'),
            func.count(FraudCheck.id).label('total_checks'),
            func.avg(FraudCheck.risk_score).label('avg_risk_score'),
            func.sum(func.case([(FraudCheck.risk_score >= 80, 1)], else_=0)).label('high_risk_count')
        ).filter(
            FraudCheck.created_at >= cutoff_date
        ).group_by('hour').order_by('hour').all()
        
        return [
            {
                "hour": int(stat.hour),
                "total_checks": stat.total_checks,
                "avg_risk_score": round(stat.avg_risk_score, 2),
                "high_risk_count": stat.high_risk_count
            }
            for stat in hourly_stats
        ]
    
    def get_rule_performance(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """Эффективность правил."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        checks = db.query(FraudCheck).filter(
            FraudCheck.created_at >= cutoff_date,
            FraudCheck.fraud_flags.isnot(None)
        ).all()
        
        rule_stats = {}
        total_checks = len(checks)
        
        for check in checks:
            try:
                import json
                flags = json.loads(check.fraud_flags)
                for flag in flags:
                    if flag not in rule_stats:
                        rule_stats[flag] = {"triggered": 0, "avg_score": 0, "scores": []}
                    rule_stats[flag]["triggered"] += 1
                    rule_stats[flag]["scores"].append(check.risk_score)
            except:
                continue
        
        # Вычисляем статистики
        for flag, stats in rule_stats.items():
            if stats["scores"]:
                stats["avg_score"] = sum(stats["scores"]) / len(stats["scores"])
                stats["trigger_rate"] = (stats["triggered"] / total_checks * 100) if total_checks > 0 else 0
                del stats["scores"]  # Удаляем сырые данные
        
        return rule_stats

# Глобальный движок аналитики
analytics_engine = AnalyticsEngine()
