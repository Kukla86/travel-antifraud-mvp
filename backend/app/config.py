from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # URL БД SQLite
    database_url: str = "sqlite:////Users/aleksandrrazumovskij/Documents/travel-antifraud-mvp/backend/antifraud.db"

    # Разрешённые источники CORS
    cors_origins: str = ""
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    # Флаги использования моков внешних сервисов
    use_email_rep_mock: bool = True
    use_bin_lookup_mock: bool = True

    # API Security
    api_key: str = "antifraud_dev_key_2024"
    rate_limit_ip: int = 60
    rate_limit_email: int = 20

    # Scoring weights
    score_geo_mismatch: int = 30
    score_temp_email: int = 25
    score_velocity: int = 20
    score_bot_activity: int = 20
    score_device_suspicious: int = 10
    score_ip_blacklisted: int = 40
    score_typing_too_fast: int = 15
    score_timezone_mismatch: int = 20

    # Recommendation thresholds
    threshold_block: int = 80
    threshold_review: int = 50

    # Cache TTL
    cache_ttl_hours: int = 24

    # Log retention
    log_retention_days: int = 90

    # Необязательные ключи
    emailrep_api_key: str | None = None

    # Сид начального blacklist IP (через запятую)
    seed_blacklist_ips: str = ""

    model_config = SettingsConfigDict(env_file=(".env", "../.env", "../../.env"), env_prefix="", case_sensitive=False)


settings = Settings()
