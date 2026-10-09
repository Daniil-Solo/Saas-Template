from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_")

    secret_key: str = Field(description="Секрет для подписи JWT")
    algorithm: str = Field(default="HS256", description="Алгоритм подписи JWT")
    access_token_ttl_minutes: int = Field(default=60, gt=0, description="Время жизни access-токена, минуты")
