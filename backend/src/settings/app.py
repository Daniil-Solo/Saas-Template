from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Общие параметры сервиса: переменные `APP` и `ENV` (без префикса)."""

    app: str = Field(default="backend", description="Имя сервиса")
    env: str = Field(default="dev", description="Окружение (dev, prod, ...)")
    base_url: str = Field(
        default="http://localhost:5173",
        validation_alias="APP_BASE_URL",
        description="Публичный адрес приложения (для ссылок в письмах), без завершающего слеша",
    )
