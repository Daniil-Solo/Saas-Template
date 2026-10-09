from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = Field(description="Хост PostgreSQL")
    port: int = Field(default=5432, description="Порт PostgreSQL")
    user: str = Field(description="Пользователь БД")
    password: str = Field(description="Пароль пользователя БД")
    name: str = Field(description="Имя БД")

    def build_url(self, driver: str) -> URL:
        return URL.create(
            drivername=driver,
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.name,
        )

    @property
    def async_url(self) -> URL:
        return self.build_url("postgresql+asyncpg")

    @property
    def sync_url(self) -> URL:
        """URL для миграций (psycopg2)."""
        return self.build_url("postgresql+psycopg2")
