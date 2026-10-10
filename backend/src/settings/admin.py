from pydantic import EmailStr, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    """Администратор, создаваемый при старте приложения, если заданы и email, и пароль."""

    model_config = SettingsConfigDict(env_prefix="ADMIN_")

    email: EmailStr | None = Field(default=None, description="Email администратора")
    password: str | None = Field(default=None, min_length=8, max_length=128, description="Пароль администратора")

    @model_validator(mode="after")
    def check_both_or_none(self) -> "AdminSettings":
        if (self.email is None) != (self.password is None):
            raise ValueError("ADMIN_EMAIL и ADMIN_PASSWORD задаются только вместе")
        return self
