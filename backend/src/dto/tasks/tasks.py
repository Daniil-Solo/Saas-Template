from typing import Any

from pydantic import EmailStr, Field

from src.constants.emails import EmailTemplate
from src.dto.common import BaseDTO


class SendEmailDTO(BaseDTO):
    to: EmailStr = Field(description="Адрес получателя")
    template: EmailTemplate = Field(description="Тип письма")
    context: dict[str, Any] = Field(description="Данные письма; проверяются по DTO контекста шаблона")


class SendInvitationEmailDTO(BaseDTO):
    invitation_id: int = Field(description="ID приглашения")
    token: str = Field(repr=False, description="Исходный токен приглашения для ссылки (в БД только хеш)")
