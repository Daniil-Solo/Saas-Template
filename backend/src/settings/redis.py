from urllib.parse import quote

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = Field(default="redis", description="Хост Redis")
    port: int = Field(default=6379, description="Порт Redis")
    db: int = Field(default=0, ge=0, description="Номер БД Redis")
    password: str | None = Field(default=None, description="Пароль Redis")

    @property
    def dsn(self) -> str:
        auth = f":{quote(self.password, safe='')}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"
