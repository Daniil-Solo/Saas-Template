from functools import lru_cache

from pydantic import BaseModel, Field

from src.settings.admin import AdminSettings
from src.settings.app import AppSettings
from src.settings.auth import AuthSettings
from src.settings.db import DBSettings
from src.settings.invitations import InvitationSettings
from src.settings.logging import LoggingSettings
from src.settings.metrics import MetricsSettings
from src.settings.sentry import SentrySettings


class Settings(BaseModel):
    """Единый объект настроек: группы читаются из окружения, каждая со своим префиксом."""

    app: AppSettings = Field(default_factory=AppSettings)
    db: DBSettings = Field(default_factory=lambda: DBSettings())
    auth: AuthSettings = Field(default_factory=lambda: AuthSettings())
    invitations: InvitationSettings = Field(default_factory=InvitationSettings)
    admin: AdminSettings = Field(default_factory=AdminSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    metrics: MetricsSettings = Field(default_factory=MetricsSettings)
    sentry: SentrySettings = Field(default_factory=SentrySettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()


__all__ = [
    "AdminSettings",
    "AppSettings",
    "AuthSettings",
    "DBSettings",
    "InvitationSettings",
    "LoggingSettings",
    "MetricsSettings",
    "SentrySettings",
    "Settings",
    "get_settings",
]
