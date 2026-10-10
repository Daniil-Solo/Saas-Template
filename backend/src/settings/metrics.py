from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MetricsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="METRICS_")

    enabled: bool = Field(default=True, description="Собирать метрики и отдавать их на /api/internal/metrics")
