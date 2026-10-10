import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import RoleNameExistsError, RoleNotFoundError
from src.constants.permissions import Permission
from src.dto.roles import RoleCreateDTO, RoleDTO, RoleUpdateDTO
from src.infrastructure.dao.roles.helpers import build_roles
from src.infrastructure.dao.roles.interface import RolesDAO
from src.infrastructure.sqlalchemy.models import role_permissions_table, roles_table

NAME_UNIQUE_CONSTRAINT = "uq_roles_name"


class SQLAlchemyRolesDAO(RolesDAO):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: RoleCreateDTO) -> RoleDTO:
        query = sa.insert(roles_table).values(name=data.name).returning(roles_table)
        try:
            result = await self.session.execute(query)
        except IntegrityError as exc:
            if NAME_UNIQUE_CONSTRAINT in str(exc.orig):
                raise RoleNameExistsError from exc
            raise
        row = result.one()
        await self._replace_permissions(row.id, data.permissions)
        return (await build_roles(self.session, [row]))[0]

    async def get_by_id(self, role_id: int) -> RoleDTO:
        result = await self.session.execute(sa.select(roles_table).where(roles_table.c.id == role_id))
        row = result.one_or_none()
        if row is None:
            raise RoleNotFoundError
        return (await build_roles(self.session, [row]))[0]

    async def get_all(self) -> list[RoleDTO]:
        result = await self.session.execute(sa.select(roles_table).order_by(roles_table.c.id))
        return await build_roles(self.session, result.all())

    async def list_by_ids(self, role_ids: list[int]) -> list[RoleDTO]:
        if not role_ids:
            return []
        query = sa.select(roles_table).where(roles_table.c.id.in_(role_ids)).order_by(roles_table.c.id)
        result = await self.session.execute(query)
        return await build_roles(self.session, result.all())

    async def update(self, role_id: int, data: RoleUpdateDTO) -> RoleDTO:
        if data.name is not None:
            query = (
                sa.update(roles_table)
                .where(roles_table.c.id == role_id)
                .values(name=data.name)
                .returning(roles_table.c.id)
            )
            try:
                result = await self.session.execute(query)
            except IntegrityError as exc:
                if NAME_UNIQUE_CONSTRAINT in str(exc.orig):
                    raise RoleNameExistsError from exc
                raise
            if result.one_or_none() is None:
                raise RoleNotFoundError
        else:
            await self.get_by_id(role_id)
        if data.permissions is not None:
            await self._replace_permissions(role_id, data.permissions)
        return await self.get_by_id(role_id)

    async def delete(self, role_id: int) -> None:
        query = sa.delete(roles_table).where(roles_table.c.id == role_id).returning(roles_table.c.id)
        result = await self.session.execute(query)
        if result.one_or_none() is None:
            raise RoleNotFoundError

    async def _replace_permissions(self, role_id: int, permissions: list[Permission]) -> None:
        await self.session.execute(sa.delete(role_permissions_table).where(role_permissions_table.c.role_id == role_id))
        unique_permissions = sorted({str(permission) for permission in permissions})
        if unique_permissions:
            await self.session.execute(
                sa.insert(role_permissions_table),
                [{"role_id": role_id, "permission": permission} for permission in unique_permissions],
            )
