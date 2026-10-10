from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO", description="Уровень логирования")
    format: Literal["console", "json"] = Field(
        default="json", description="Формат логов: console - для человека, json - по записи на строку"
    )
