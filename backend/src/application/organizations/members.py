from dependency_injector.wiring import Provide, inject

from src.application.exceptions import OrganizationCreatorCannotLeaveError, PermissionDeniedError, RoleNotFoundError
from src.constants.permissions import Permission
from src.di.container import Container
from src.dto.common import SuccessOperationDTO
from src.dto.organizations import MemberDTO, MemberRolesUpdateDTO, OrganizationAccessDTO
from src.infrastructure.sqlalchemy.uow import UnitOfWork


@inject
async def list_for_organization(
    access: OrganizationAccessDTO,
    uow: UnitOfWork = Provide[Container.uow],
) -> list[MemberDTO]:
    async with uow.connection():
        return await uow.members.list_for_organization(access.organization_id)


@inject
async def update_roles(
    member_id: int,
    data: MemberRolesUpdateDTO,
    access: OrganizationAccessDTO,
    uow: UnitOfWork = Provide[Container.uow],
) -> MemberDTO:
    """Заменяет роли участника. Право members:manage проверяет зависимость роутера."""
    role_ids = sorted(set(data.role_ids))
    async with uow.connection() as conn, conn.transaction():
        await uow.members.get(access.organization_id, member_id)
        found_roles = await uow.roles.list_by_ids(role_ids)
        if len(found_roles) != len(role_ids):
            raise RoleNotFoundError
        await uow.members.set_roles(member_id, role_ids)
        return await uow.members.get(access.organization_id, member_id)


@inject
async def remove(
    member_id: int,
    access: OrganizationAccessDTO,
    uow: UnitOfWork = Provide[Container.uow],
) -> SuccessOperationDTO:
    """Исключает участника или выводит из организации самого пользователя (member_id совпадает с его участием)."""
    async with uow.connection():
        member = await uow.members.get(access.organization_id, member_id)
        is_self = member.user.id == access.user_id
        if not is_self and Permission.MEMBERS_MANAGE not in access.permissions:
            raise PermissionDeniedError
        if member.is_creator:
            raise OrganizationCreatorCannotLeaveError
        await uow.members.delete(member_id)
    return SuccessOperationDTO()
