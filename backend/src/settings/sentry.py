from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SentrySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SENTRY_")

    dsn: str | None = Field(default=None, description="DSN Sentry; не задан - отправка ошибок выключена")
    environment: str | None = Field(default=None, description="Окружение в Sentry; по умолчанию значение ENV")
    release: str | None = Field(default=None, description="Версия приложения в Sentry")
    traces_sample_rate: float = Field(default=0, ge=0, le=1, description="Доля трассируемых запросов")

    @field_validator("dsn", "environment", "release", mode="before")
    @classmethod
    def empty_to_none(cls, value: Any) -> Any:
        """Пустая строка в окружении (`SENTRY_DSN=`) приравнивается к «не задано»."""
        if isinstance(value, str) and not value.strip():
            return None
        return value
