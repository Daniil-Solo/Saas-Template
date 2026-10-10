from dependency_injector.wiring import Provide, inject

from src.di.container import Container
from src.dto.organizations import OrganizationAccessDTO, OrganizationCreateDTO, OrganizationDetailDTO, OrganizationDTO
from src.dto.users import UserDTO
from src.infrastructure.sqlalchemy.uow import UnitOfWork


@inject
async def create(
    data: OrganizationCreateDTO,
    user: UserDTO,
    uow: UnitOfWork = Provide[Container.uow],
) -> OrganizationDTO:
    async with uow.connection() as conn, conn.transaction():
        organization = await uow.organizations.create(data.name, user.id)
        await uow.members.create(organization.id, user.id)
    return organization


@inject
async def list_for_user(
    user: UserDTO,
    uow: UnitOfWork = Provide[Container.uow],
) -> list[OrganizationDTO]:
    async with uow.connection():
        return await uow.organizations.list_for_user(user.id)


@inject
async def get_access(
    organization_id: int,
    user: UserDTO,
    uow: UnitOfWork = Provide[Container.uow],
) -> OrganizationAccessDTO:
    """Доступ пользователя к организации; не участник -> OrganizationNotFoundError."""
    async with uow.connection():
        return await uow.members.get_access(organization_id, user.id)


@inject
async def get_by_id(
    access: OrganizationAccessDTO,
    uow: UnitOfWork = Provide[Container.uow],
) -> OrganizationDetailDTO:
    async with uow.connection():
        organization = await uow.organizations.get_by_id(access.organization_id)
    return OrganizationDetailDTO(
        **organization.model_dump(),
        permissions=sorted(access.permissions),
        is_creator=access.is_creator,
    )
