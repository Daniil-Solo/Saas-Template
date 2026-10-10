from fastapi import APIRouter, Depends, status

from src.application.invitations import invitations as invitations_service
from src.dto.common import ErrorDTO
from src.dto.invitations import InvitationPreviewDTO
from src.dto.organizations import OrganizationDTO
from src.dto.users import UserDTO
from src.interfaces.api.dependencies import get_current_user

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.get(
    "/{token}",
    response_model=InvitationPreviewDTO,
    summary="Просмотр приглашения по токену",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorDTO, "description": "Приглашение не найдено (invitation_not_found)"}
    },
)
async def preview_invitation_endpoint(
    token: str,
    user: UserDTO = Depends(get_current_user),
) -> InvitationPreviewDTO:
    return await invitations_service.preview(token)


@router.post(
    "/{token}/accept",
    response_model=OrganizationDTO,
    summary="Принять приглашение",
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ErrorDTO, "description": "Другой email (invitation_email_mismatch)"},
        status.HTTP_404_NOT_FOUND: {"model": ErrorDTO, "description": "Приглашение не найдено (invitation_not_found)"},
        status.HTTP_409_CONFLICT: {
            "model": ErrorDTO,
            "description": "Приглашение принято или отозвано (invitation_not_pending), "
            "пользователь уже участник (member_already_exists)",
        },
        status.HTTP_410_GONE: {"model": ErrorDTO, "description": "Срок истёк (invitation_expired)"},
    },
)
async def accept_invitation_endpoint(
    token: str,
    user: UserDTO = Depends(get_current_user),
) -> OrganizationDTO:
    return await invitations_service.accept(token, user)
