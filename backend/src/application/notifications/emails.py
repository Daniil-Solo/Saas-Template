import datetime
import uuid

from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel
import structlog

from src.application.exceptions import InvitationNotFoundError
from src.constants.emails import EmailTemplate
from src.constants.invitations import InvitationStatus
from src.constants.tasks import TaskName
from src.di.container import Container
from src.dto.emails import (
    EMAIL_CONTEXTS,
    EmailEnqueuedDTO,
    EmailMessage,
    EmailSendRequestDTO,
    EmailTemplateInfoDTO,
    InvitationEmailContext,
)
from src.dto.tasks import SendEmailDTO
from src.dto.users import UserDTO
from src.infrastructure.auth import invitation_token
from src.infrastructure.email_sender.interface import EmailSender
from src.infrastructure.email_templater.interface import EmailTemplater
from src.infrastructure.queue.interface import TaskQueue
from src.infrastructure.sqlalchemy.uow import UnitOfWork
from src.settings import AppSettings, EmailSettings

logger = structlog.get_logger(__name__)

DEFAULT_INVITER_NAME = "Администратор"


@inject
async def send(
    to: str,
    template: EmailTemplate,
    context: BaseModel,
    sender: EmailSender = Provide[Container.email_sender],
    templater: EmailTemplater = Provide[Container.email_templater],
    email_settings: EmailSettings = Provide[Container.email_settings],
) -> None:
    """Рендерит письмо и отправляет его; ошибки отправки (`EmailSendError`) обрабатывает вызывающая задача."""
    rendered = templater.render(template, context)
    await sender.send(EmailMessage(to=to, subject=rendered.subject, html=rendered.html, text=rendered.text))
    logger.info("email_sent", template=template.value, backend=email_settings.backend)


@inject
async def send_invitation(
    invitation_id: int,
    token: str,
    uow: UnitOfWork = Provide[Container.uow],
    app_settings: AppSettings = Provide[Container.app_settings],
) -> bool:
    """Отправляет письмо-приглашение, если приглашение ещё действует. Возвращает, было ли письмо отправлено."""
    now = datetime.datetime.now(datetime.UTC)
    async with uow.connection():
        try:
            record = await uow.invitations.get_by_token_hash(invitation_token.hash_token(token))
        except InvitationNotFoundError:
            logger.info("email_skipped", template=EmailTemplate.INVITATION.value, reason="invitation_not_found")
            return False
        if record.id != invitation_id:
            logger.info("email_skipped", template=EmailTemplate.INVITATION.value, reason="invitation_mismatch")
            return False
        if record.status != InvitationStatus.PENDING or record.expires_at <= now:
            logger.info("email_skipped", template=EmailTemplate.INVITATION.value, reason="invitation_not_active")
            return False
        organization = await uow.organizations.get_by_id(record.organization_id)
        roles = (await uow.invitations.get_roles([record.id])).get(record.id, [])
        inviter_name = DEFAULT_INVITER_NAME
        if record.invited_by_id is not None:
            inviter_name = (await uow.users.get_by_id(record.invited_by_id)).fullname

    context = InvitationEmailContext(
        invited_by_name=inviter_name,
        organization_name=organization.name,
        role_names=[role.name for role in roles],
        expires_at=record.expires_at,
        accept_url=f"{app_settings.base_url.rstrip('/')}/invitations/{token}",
    )
    await send(record.email, EmailTemplate.INVITATION, context)
    return True


@inject
async def enqueue_email(
    data: EmailSendRequestDTO,
    admin: UserDTO,
    queue: TaskQueue = Provide[Container.task_queue],
) -> EmailEnqueuedDTO:
    """Ставит письмо по типу шаблона и данным; `admin` - текущий администратор (проверен зависимостью роутера)."""
    context = EMAIL_CONTEXTS[data.template].model_validate(data.payload)
    payload = SendEmailDTO(to=data.to, template=data.template, context=context.model_dump(mode="json"))
    job_id = f"email-{data.idempotency_key or uuid.uuid4().hex}"
    await queue.enqueue(TaskName.SEND_EMAIL, payload, job_id=job_id)
    return EmailEnqueuedDTO(job_id=job_id)


def get_templates() -> list[EmailTemplateInfoDTO]:
    return [
        EmailTemplateInfoDTO(template=template, payload_schema=context.model_json_schema())
        for template, context in EMAIL_CONTEXTS.items()
    ]
