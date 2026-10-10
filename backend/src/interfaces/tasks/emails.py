from typing import Any

from arq import Retry
from pydantic import ValidationError
import structlog

from src.application.notifications import emails as emails_service
from src.constants.tasks import TaskName
from src.dto.emails import EMAIL_CONTEXTS
from src.dto.tasks import SendEmailDTO, SendInvitationEmailDTO
from src.infrastructure.email_sender.exceptions import EmailPermanentError, EmailTemporaryError

logger = structlog.get_logger(__name__)

MAX_TRIES = 5
RETRY_BASE_SECONDS = 30


def retry_delay(attempt: int) -> int:
    """Пауза перед следующей попыткой: 30 с, 2 мин, 4.5 мин, 8 мин."""
    return RETRY_BASE_SECONDS * attempt**2


def _handle_send_error(task: TaskName, ctx: dict[str, Any], error: Exception) -> None:
    """Временная ошибка -> Retry (пока есть попытки), иначе только лог `error` без адреса и токена."""
    attempt = int(ctx.get("job_try", 1))
    job_id = ctx.get("job_id")
    if isinstance(error, EmailTemporaryError) and attempt < MAX_TRIES:
        logger.warning("email_failed", task=task.value, job_id=job_id, attempt=attempt, error=type(error).__name__)
        raise Retry(defer=retry_delay(attempt)) from error
    logger.error("email_failed", task=task.value, job_id=job_id, attempt=attempt, error=type(error).__name__)


async def send_email(ctx: dict[str, Any], payload: dict[str, Any]) -> None:
    task = TaskName.SEND_EMAIL
    try:
        data = SendEmailDTO.model_validate(payload)
        context = EMAIL_CONTEXTS[data.template].model_validate(data.context)
    except ValidationError:
        # Повтор не поможет: данные не изменятся
        logger.error("email_failed", task=task.value, job_id=ctx.get("job_id"), error="invalid_payload")
        return
    try:
        await emails_service.send(data.to, data.template, context)
    except (EmailTemporaryError, EmailPermanentError) as exc:
        _handle_send_error(task, ctx, exc)


async def send_invitation_email(ctx: dict[str, Any], payload: dict[str, Any]) -> None:
    task = TaskName.SEND_INVITATION_EMAIL
    data = SendInvitationEmailDTO.model_validate(payload)
    try:
        await emails_service.send_invitation(data.invitation_id, data.token)
    except (EmailTemporaryError, EmailPermanentError) as exc:
        _handle_send_error(task, ctx, exc)
