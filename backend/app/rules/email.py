from __future__ import annotations
from typing import Optional, Set
from ..config import settings
from pydantic import BaseModel
import re

# Расширенный список временных email доменов
TEMP_DOMAINS: Set[str] = {
    "mailinator.com", "yopmail.com", "tempmail.com", "10minutemail.com",
    "guerrillamail.com", "maildrop.cc", "temp-mail.org", "throwaway.email",
    "getnada.com", "mailnesia.com", "sharklasers.com", "guerrillamail.biz",
    "guerrillamail.de", "guerrillamail.info", "guerrillamail.net",
    "guerrillamail.org", "pokemail.net", "spam4.me", "bccto.me",
    "chacuo.net", "dispostable.com", "mailcatch.com", "mailmetrash.com",
    "trashmail.net", "trashmail.com", "trashmail.org", "trashmail.ws",
    "trashmail.de", "trashmail.fr", "trashmail.it", "trashmail.es",
    "trashmail.ru", "trashmail.pl", "trashmail.nl", "trashmail.se",
    "trashmail.no", "trashmail.dk", "trashmail.fi", "trashmail.be",
    "trashmail.at", "trashmail.ch", "trashmail.cz", "trashmail.sk",
    "trashmail.hu", "trashmail.ro", "trashmail.bg", "trashmail.hr",
    "trashmail.si", "trashmail.ee", "trashmail.lv", "trashmail.lt",
    "trashmail.ua", "trashmail.by", "trashmail.kz", "trashmail.kg",
    "trashmail.tj", "trashmail.tm", "trashmail.uz", "trashmail.az",
    "trashmail.am", "trashmail.ge", "trashmail.md", "trashmail.al",
    "trashmail.mk", "trashmail.me", "trashmail.rs", "trashmail.ba",
    "trashmail.mn", "trashmail.kp", "trashmail.kr", "trashmail.jp",
    "trashmail.cn", "trashmail.tw", "trashmail.hk", "trashmail.mo",
    "trashmail.sg", "trashmail.my", "trashmail.th", "trashmail.vn",
    "trashmail.kh", "trashmail.la", "trashmail.mm", "trashmail.bd",
    "trashmail.lk", "trashmail.mv", "trashmail.bt", "trashmail.np",
    "trashmail.pk", "trashmail.af", "trashmail.ir", "trashmail.iq",
    "trashmail.sy", "trashmail.lb", "trashmail.jo", "trashmail.il",
    "trashmail.ps", "trashmail.eg", "trashmail.ly", "trashmail.tn",
    "trashmail.dz", "trashmail.ma", "trashmail.sd", "trashmail.ss",
    "trashmail.et", "trashmail.er", "trashmail.dj", "trashmail.so",
    "trashmail.ke", "trashmail.ug", "trashmail.tz", "trashmail.rw",
    "trashmail.bi", "trashmail.mg", "trashmail.mu", "trashmail.sc",
    "trashmail.km", "trashmail.yt", "trashmail.re", "trashmail.mz",
    "trashmail.mw", "trashmail.zm", "trashmail.zw", "trashmail.bw",
    "trashmail.na", "trashmail.sz", "trashmail.ls", "trashmail.za",
    "trashmail.ao", "trashmail.cd", "trashmail.cg", "trashmail.cm",
    "trashmail.cf", "trashmail.td", "trashmail.ne", "trashmail.ng",
    "trashmail.bj", "trashmail.tg", "trashmail.gh", "trashmail.bf",
    "trashmail.ci", "trashmail.lr", "trashmail.sl", "trashmail.gn",
    "trashmail.gw", "trashmail.gm", "trashmail.sn", "trashmail.ml",
    "trashmail.mr", "trashmail.dz", "trashmail.tn", "trashmail.ly",
    "trashmail.eg", "trashmail.sd", "trashmail.ss", "trashmail.et",
    "trashmail.er", "trashmail.dj", "trashmail.so", "trashmail.ke",
    "trashmail.ug", "trashmail.tz", "trashmail.rw", "trashmail.bi",
    "trashmail.mg", "trashmail.mu", "trashmail.sc", "trashmail.km",
    "trashmail.yt", "trashmail.re", "trashmail.mz", "trashmail.mw",
    "trashmail.zm", "trashmail.zw", "trashmail.bw", "trashmail.na",
    "trashmail.sz", "trashmail.ls", "trashmail.za", "trashmail.ao",
    "trashmail.cd", "trashmail.cg", "trashmail.cm", "trashmail.cf",
    "trashmail.td", "trashmail.ne", "trashmail.ng", "trashmail.bj",
    "trashmail.tg", "trashmail.gh", "trashmail.bf", "trashmail.ci",
    "trashmail.lr", "trashmail.sl", "trashmail.gn", "trashmail.gw",
    "trashmail.gm", "trashmail.sn", "trashmail.ml", "trashmail.mr"
}

# Паттерны для подозрительных email
SUSPICIOUS_PATTERNS = [
    r'^[a-z0-9]{6,}@',  # Только цифры и буквы в начале
    r'^[0-9]{6,}@',     # Только цифры в начале
    r'^[a-z]{6,}@',     # Только буквы в начале
    r'^.{1,3}@',        # Очень короткие имена
    r'^.{50,}@',        # Очень длинные имена
    r'[0-9]{4,}@',      # Много цифр подряд
    r'[a-z]{4,}@',      # Много букв подряд
    r'[0-9]{2,}[a-z]{2,}[0-9]{2,}@',  # Чередование цифр и букв
]


class EmailRuleResult(BaseModel):
    score_delta: int
    fraud_flag: Optional[str] = None


def check_email_reputation(email: str) -> EmailRuleResult:
    if not email or "@" not in email:
        return EmailRuleResult(score_delta=settings.score_temp_email, fraud_flag="invalid_email")
    
    # Извлекаем домен
    domain = email.split("@")[-1].lower().strip()
    
    # Проверяем временные домены
    if domain in TEMP_DOMAINS:
        return EmailRuleResult(score_delta=settings.score_temp_email, fraud_flag="temporary_email")
    
    # Проверяем подозрительные паттерны
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, email.lower()):
            return EmailRuleResult(score_delta=settings.score_temp_email // 2, fraud_flag="suspicious_email")
    
    # Проверяем валидность email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return EmailRuleResult(score_delta=settings.score_temp_email, fraud_flag="invalid_email")
    
    return EmailRuleResult(score_delta=0, fraud_flag=None)
