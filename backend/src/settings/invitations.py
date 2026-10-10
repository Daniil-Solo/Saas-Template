from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class InvitationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INVITATION_")

    ttl_days: int = Field(default=7, gt=0, description="Срок действия приглашения, дни")
