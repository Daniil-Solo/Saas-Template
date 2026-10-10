from typing import Any

from fastapi import APIRouter, Depends, status

from src.application.invitations import invitations as invitations_service
from src.application.organizations import members as members_service
from src.application.organizations import organizations as organizations_service
from src.dto.common import ErrorDTO, SuccessOperationDTO
from src.dto.invitations import InvitationCreatedDTO, InvitationCreateDTO, InvitationDTO
from src.dto.organizations import (
    MemberDTO,
    MemberRolesUpdateDTO,
    OrganizationAccessDTO,
    OrganizationCreateDTO,
    OrganizationDetailDTO,
    OrganizationDTO,
)
from src.dto.users import UserDTO
from src.interfaces.api.dependencies import (
    get_current_user,
    get_organization_access,
    require_invitations_manage,
    require_members_manage,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])

NOT_MEMBER_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorDTO,
        "description": "Организация не найдена или пользователь не её участник (organization_not_found)",
    }
}
PERMISSION_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {"model": ErrorDTO, "description": "Нет нужного права (permission_denied)"}
}


@router.post("", response_model=OrganizationDTO, summary="Создать организацию")
async def create_organization_endpoint(
    data: OrganizationCreateDTO,
    user: UserDTO = Depends(get_current_user),
) -> OrganizationDTO:
    return await organizations_service.create(data, user)


@router.get("", response_model=list[OrganizationDTO], summary="Мои организации")
async def list_organizations_endpoint(user: UserDTO = Depends(get_current_user)) -> list[OrganizationDTO]:
    return await organizations_service.list_for_user(user)


@router.get(
    "/{org_id}",
    response_model=OrganizationDetailDTO,
    summary="Организация с правами текущего пользователя",
    responses=NOT_MEMBER_RESPONSE,
)
async def get_organization_endpoint(
    access: OrganizationAccessDTO = Depends(get_organization_access),
) -> OrganizationDetailDTO:
    return await organizations_service.get_by_id(access)


@router.get(
    "/{org_id}/members",
    response_model=list[MemberDTO],
    summary="Участники организации",
    responses=NOT_MEMBER_RESPONSE,
)
async def list_members_endpoint(
    access: OrganizationAccessDTO = Depends(get_organization_access),
) -> list[MemberDTO]:
    return await members_service.list_for_organization(access)


@router.put(
    "/{org_id}/members/{member_id}/roles",
    response_model=MemberDTO,
    summary="Заменить роли участника",
    responses={**NOT_MEMBER_RESPONSE, **PERMISSION_RESPONSE},
)
async def update_member_roles_endpoint(
    member_id: int,
    data: MemberRolesUpdateDTO,
    access: OrganizationAccessDTO = Depends(require_members_manage),
) -> MemberDTO:
    return await members_service.update_roles(member_id, data, access)


@router.delete(
    "/{org_id}/members/{member_id}",
    response_model=SuccessOperationDTO,
    summary="Исключить участника или выйти из организации",
    responses={
        **NOT_MEMBER_RESPONSE,
        **PERMISSION_RESPONSE,
        status.HTTP_409_CONFLICT: {
            "model": ErrorDTO,
            "description": "Создатель не может выйти или быть исключён (organization_creator_cannot_leave)",
        },
    },
)
async def remove_member_endpoint(
    member_id: int,
    access: OrganizationAccessDTO = Depends(get_organization_access),
) -> SuccessOperationDTO:
    return await members_service.remove(member_id, access)


@router.post(
    "/{org_id}/invitations",
    response_model=InvitationCreatedDTO,
    summary="Создать приглашение",
    responses={**NOT_MEMBER_RESPONSE, **PERMISSION_RESPONSE},
)
async def create_invitation_endpoint(
    data: InvitationCreateDTO,
    access: OrganizationAccessDTO = Depends(require_invitations_manage),
) -> InvitationCreatedDTO:
    return await invitations_service.create(data, access)


@router.get(
    "/{org_id}/invitations",
    response_model=list[InvitationDTO],
    summary="Приглашения организации",
    responses={**NOT_MEMBER_RESPONSE, **PERMISSION_RESPONSE},
)
async def list_invitations_endpoint(
    access: OrganizationAccessDTO = Depends(require_invitations_manage),
) -> list[InvitationDTO]:
    return await invitations_service.get_all(access)


@router.delete(
    "/{org_id}/invitations/{invitation_id}",
    response_model=SuccessOperationDTO,
    summary="Отозвать приглашение",
    responses={**NOT_MEMBER_RESPONSE, **PERMISSION_RESPONSE},
)
async def revoke_invitation_endpoint(
    invitation_id: int,
    access: OrganizationAccessDTO = Depends(require_invitations_manage),
) -> SuccessOperationDTO:
    return await invitations_service.revoke(invitation_id, access)
