from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.application.notifications import emails as emails_service
from src.dto.common import ErrorDTO
from src.dto.emails import EMAIL_CONTEXTS, EmailEnqueuedDTO, EmailSendRequestDTO, EmailTemplateInfoDTO
from src.dto.users import UserDTO
from src.interfaces.api.dependencies import get_current_admin

router = APIRouter(prefix="/notifications", tags=["notifications"])

ADMIN_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {"model": ErrorDTO, "description": "Не администратор системы (admin_required)"}
}


def _validate_payload(data: EmailSendRequestDTO) -> None:
    """Проверяет payload по DTO контекста; ошибка -> 422 с путём поля (body.payload.<поле>)."""
    try:
        EMAIL_CONTEXTS[data.template].model_validate(data.payload)
    except ValidationError as exc:
        errors = [
            {**error, "loc": ("body", "payload", *error["loc"])}
            for error in exc.errors(include_url=False, include_context=False, include_input=False)
        ]
        raise RequestValidationError(errors) from exc


@router.post(
    "/email",
    response_model=EmailEnqueuedDTO,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Поставить письмо в очередь (администратор)",
    responses=ADMIN_RESPONSE,
)
async def send_email_endpoint(
    data: EmailSendRequestDTO,
    admin: UserDTO = Depends(get_current_admin),
) -> EmailEnqueuedDTO:
    _validate_payload(data)
    return await emails_service.enqueue_email(data, admin)


@router.get(
    "/templates",
    response_model=list[EmailTemplateInfoDTO],
    summary="Типы писем и схемы их данных (администратор)",
    responses=ADMIN_RESPONSE,
)
async def list_templates_endpoint(admin: UserDTO = Depends(get_current_admin)) -> list[EmailTemplateInfoDTO]:
    return emails_service.get_templates()
