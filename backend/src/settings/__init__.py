from functools import lru_cache

from pydantic import BaseModel, Field, model_validator

from src.settings.admin import AdminSettings
from src.settings.app import AppSettings
from src.settings.auth import AuthSettings
from src.settings.db import DBSettings
from src.settings.email import EmailSettings, MailerooSettings, SmtpSettings
from src.settings.invitations import InvitationSettings
from src.settings.logging import LoggingSettings
from src.settings.metrics import MetricsSettings
from src.settings.redis import RedisSettings
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
    redis: RedisSettings = Field(default_factory=RedisSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)
    maileroo: MailerooSettings = Field(default_factory=MailerooSettings)

    @model_validator(mode="after")
    def check_email_backend(self) -> "Settings":
        """Проверяет поля только выбранного коннектора писем; сообщение называет переменную."""
        if self.email.backend == "smtp":
            if not self.smtp.host:
                raise ValueError("EMAIL_SMTP_HOST обязателен при EMAIL_BACKEND=smtp")
            if (self.smtp.username is None) != (self.smtp.password is None):
                raise ValueError("EMAIL_SMTP_USERNAME и EMAIL_SMTP_PASSWORD задаются только вместе")
        elif self.email.backend == "maileroo" and not self.maileroo.api_key:
            raise ValueError("EMAIL_MAILEROO_API_KEY обязателен при EMAIL_BACKEND=maileroo")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


__all__ = [
    "AdminSettings",
    "AppSettings",
    "AuthSettings",
    "DBSettings",
    "EmailSettings",
    "InvitationSettings",
    "LoggingSettings",
    "MailerooSettings",
    "MetricsSettings",
    "RedisSettings",
    "SentrySettings",
    "SmtpSettings",
    "Settings",
    "get_settings",
]
