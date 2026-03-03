from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from .env file"""

    # Обязательные параметры из .env
    database_url: str
    secret_key: str

    # Параметры с значениями по умолчанию
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"

    # smtp
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_from_name: str = "Booking Service"

    model_config = ConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="UTF-8",
        case_sensitive=False,
    )


settings = Settings()
