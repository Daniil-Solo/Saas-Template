from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmailSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMAIL_", populate_by_name=True)

    backend: Literal["console", "smtp", "maileroo"] = Field(
        default="console", description="Коннектор отправки писем: console (в лог), smtp, maileroo"
    )
    from_address: str = Field(
        default="noreply@example.com", validation_alias="EMAIL_FROM", description="Адрес отправителя"
    )
    from_display_name: str = Field(default="App", description="Имя отправителя и название сервиса в шапке письма")


class SmtpSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMAIL_SMTP_")

    host: str | None = Field(default=None, description="Хост SMTP-сервера")
    port: int = Field(default=587, description="Порт SMTP-сервера")
    username: str | None = Field(default=None, description="Логин SMTP")
    password: str | None = Field(default=None, description="Пароль SMTP")
    tls: Literal["starttls", "ssl", "none"] = Field(default="starttls", description="Шифрование соединения")
    timeout: float = Field(default=10, gt=0, description="Таймаут соединения, секунды")

    @model_validator(mode="before")
    @classmethod
    def empty_to_none(cls, data: object) -> object:
        if isinstance(data, dict):
            return {key: (None if value == "" else value) for key, value in data.items()}
        return data


class MailerooSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMAIL_MAILEROO_")

    api_key: str | None = Field(default=None, description="API-ключ Maileroo")

    @model_validator(mode="before")
    @classmethod
    def empty_to_none(cls, data: object) -> object:
        if isinstance(data, dict):
            return {key: (None if value == "" else value) for key, value in data.items()}
        return data
