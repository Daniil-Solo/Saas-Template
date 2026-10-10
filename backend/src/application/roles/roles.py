from dependency_injector.wiring import Provide, inject

from src.di.container import Container
from src.dto.common import SuccessOperationDTO
from src.dto.roles import RoleCreateDTO, RoleDTO, RoleUpdateDTO
from src.infrastructure.sqlalchemy.uow import UnitOfWork


@inject
async def get_all(uow: UnitOfWork = Provide[Container.uow]) -> list[RoleDTO]:
    async with uow.connection():
        return await uow.roles.get_all()


@inject
async def create(data: RoleCreateDTO, uow: UnitOfWork = Provide[Container.uow]) -> RoleDTO:
    async with uow.connection() as conn, conn.transaction():
        return await uow.roles.create(data)


@inject
async def update(role_id: int, data: RoleUpdateDTO, uow: UnitOfWork = Provide[Container.uow]) -> RoleDTO:
    async with uow.connection() as conn, conn.transaction():
        return await uow.roles.update(role_id, data)


@inject
async def delete(role_id: int, uow: UnitOfWork = Provide[Container.uow]) -> SuccessOperationDTO:
    async with uow.connection():
        await uow.roles.delete(role_id)
    return SuccessOperationDTO()
