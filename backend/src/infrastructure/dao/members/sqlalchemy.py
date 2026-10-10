from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import MemberAlreadyExistsError, MemberNotFoundError, OrganizationNotFoundError
from src.constants.permissions import Permission
from src.dto.organizations import MemberDTO, MemberUserDTO, OrganizationAccessDTO
from src.dto.roles import RoleDTO
from src.infrastructure.dao.members.interface import MembersDAO
from src.infrastructure.dao.roles.helpers import build_roles
from src.infrastructure.sqlalchemy.models import (
    member_roles_table,
    organization_members_table,
    organizations_table,
    role_permissions_table,
    roles_table,
    users_table,
)

MEMBER_UNIQUE_CONSTRAINT = "uq_organization_members_organization_user"


class SQLAlchemyMembersDAO(MembersDAO):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, organization_id: int, user_id: int) -> int:
        query = (
            sa.insert(organization_members_table)
            .values(organization_id=organization_id, user_id=user_id)
            .returning(organization_members_table.c.id)
        )
        try:
            result = await self.session.execute(query)
        except IntegrityError as exc:
            if MEMBER_UNIQUE_CONSTRAINT in str(exc.orig):
                raise MemberAlreadyExistsError from exc
            raise
        return int(result.scalar_one())

    async def get_access(self, organization_id: int, user_id: int) -> OrganizationAccessDTO:
        query = (
            sa.select(
                organization_members_table.c.id,
                (organizations_table.c.created_by_id == organization_members_table.c.user_id).label("is_creator"),
            )
            .join(organizations_table, organizations_table.c.id == organization_members_table.c.organization_id)
            .where(
                organization_members_table.c.organization_id == organization_id,
                organization_members_table.c.user_id == user_id,
            )
        )
        row = (await self.session.execute(query)).one_or_none()
        if row is None:
            raise OrganizationNotFoundError
        if row.is_creator:
            permissions = set(Permission)
        else:
            perm_query = (
                sa.select(role_permissions_table.c.permission)
                .join(member_roles_table, member_roles_table.c.role_id == role_permissions_table.c.role_id)
                .where(member_roles_table.c.member_id == row.id)
                .distinct()
            )
            permissions = {Permission(value) for value in (await self.session.execute(perm_query)).scalars()}
        return OrganizationAccessDTO(
            organization_id=organization_id,
            member_id=row.id,
            user_id=user_id,
            permissions=permissions,
            is_creator=row.is_creator,
        )

    async def get(self, organization_id: int, member_id: int) -> MemberDTO:
        query = self._members_query().where(
            organization_members_table.c.organization_id == organization_id,
            organization_members_table.c.id == member_id,
        )
        rows = (await self.session.execute(query)).all()
        if not rows:
            raise MemberNotFoundError
        return (await self._build(rows))[0]

    async def list_for_organization(self, organization_id: int) -> list[MemberDTO]:
        query = (
            self._members_query()
            .where(organization_members_table.c.organization_id == organization_id)
            .order_by(organization_members_table.c.id)
        )
        rows = (await self.session.execute(query)).all()
        return await self._build(rows)

    async def exists_by_email(self, organization_id: int, email: str) -> bool:
        query = (
            sa.select(organization_members_table.c.id)
            .join(users_table, users_table.c.id == organization_members_table.c.user_id)
            .where(organization_members_table.c.organization_id == organization_id, users_table.c.email == email)
        )
        return (await self.session.execute(query)).first() is not None

    async def set_roles(self, member_id: int, role_ids: list[int]) -> None:
        await self.session.execute(sa.delete(member_roles_table).where(member_roles_table.c.member_id == member_id))
        unique_ids = sorted(set(role_ids))
        if unique_ids:
            await self.session.execute(
                sa.insert(member_roles_table),
                [{"member_id": member_id, "role_id": role_id} for role_id in unique_ids],
            )

    async def delete(self, member_id: int) -> None:
        query = (
            sa.delete(organization_members_table)
            .where(organization_members_table.c.id == member_id)
            .returning(organization_members_table.c.id)
        )
        if (await self.session.execute(query)).one_or_none() is None:
            raise MemberNotFoundError

    @staticmethod
    def _members_query() -> sa.Select[Any]:
        return (
            sa.select(
                organization_members_table.c.id,
                organization_members_table.c.organization_id,
                organization_members_table.c.created_at,
                users_table.c.id.label("user_id"),
                users_table.c.fullname,
                users_table.c.email,
                (organizations_table.c.created_by_id == organization_members_table.c.user_id).label("is_creator"),
            )
            .join(users_table, users_table.c.id == organization_members_table.c.user_id)
            .join(organizations_table, organizations_table.c.id == organization_members_table.c.organization_id)
        )

    async def _build(self, rows: Sequence[Row[Any]]) -> list[MemberDTO]:
        member_ids = [row.id for row in rows]
        roles_query = (
            sa.select(roles_table, member_roles_table.c.member_id)
            .join(member_roles_table, member_roles_table.c.role_id == roles_table.c.id)
            .where(member_roles_table.c.member_id.in_(member_ids))
            .order_by(roles_table.c.id)
        )
        role_rows = (await self.session.execute(roles_query)).all()
        roles = await build_roles(self.session, role_rows)
        roles_by_member: dict[int, list[RoleDTO]] = {}
        for role_row, role in zip(role_rows, roles, strict=True):
            roles_by_member.setdefault(role_row.member_id, []).append(role)
        return [
            MemberDTO(
                id=row.id,
                organization_id=row.organization_id,
                user=MemberUserDTO(id=row.user_id, fullname=row.fullname, email=row.email),
                roles=roles_by_member.get(row.id, []),
                is_creator=row.is_creator,
                created_at=row.created_at,
            )
            for row in rows
        ]
