import datetime
from typing import Any

from pydantic import ConfigDict, EmailStr, Field

from src.constants.emails import EmailTemplate
from src.dto.common import BaseDTO


class EmailContextDTO(BaseDTO):
    """Базовый класс контекста письма: лишние поля запрещены."""

    model_config = ConfigDict(extra="forbid")


class WelcomeEmailContext(EmailContextDTO):
    fullname: str = Field(min_length=1, max_length=255, description="ФИО получателя")
    login_url: str = Field(min_length=1, max_length=2048, description="Ссылка на страницу входа")


class InvitationEmailContext(EmailContextDTO):
    invited_by_name: str = Field(min_length=1, max_length=255, description="Имя пригласившего")
    organization_name: str = Field(min_length=1, max_length=255, description="Название организации")
    role_names: list[str] = Field(description="Названия ролей, которые получит приглашённый")
    expires_at: datetime.datetime = Field(description="Срок действия приглашения")
    accept_url: str = Field(min_length=1, max_length=2048, description="Ссылка для принятия приглашения")


class EmailMessage(BaseDTO):
    """Готовое к отправке письмо; адрес и имя отправителя берёт коннектор из настроек."""

    to: str = Field(description="Адрес получателя")
    subject: str = Field(description="Тема")
    html: str = Field(description="HTML-версия")
    text: str = Field(description="Текстовая версия")


class RenderedEmail(BaseDTO):
    subject: str = Field(description="Тема")
    html: str = Field(description="HTML-версия")
    text: str = Field(description="Текстовая версия")


class EmailSendRequestDTO(BaseDTO):
    template: EmailTemplate = Field(description="Тип письма (см. GET /api/v1/notifications/templates)")
    to: EmailStr = Field(description="Адрес получателя")
    payload: dict[str, Any] = Field(description="Данные письма; схема зависит от шаблона")
    idempotency_key: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z0-9-]{1,64}$",
        description="Ключ идемпотентности: повторный запрос с тем же ключом не ставит письмо второй раз, "
        "пока первое в очереди или выполняется",
    )


class EmailEnqueuedDTO(BaseDTO):
    job_id: str = Field(description="ID поставленной задачи")


class EmailTemplateInfoDTO(BaseDTO):
    template: EmailTemplate = Field(description="Тип письма")
    payload_schema: dict[str, Any] = Field(description="JSON Schema данных письма (payload)")
