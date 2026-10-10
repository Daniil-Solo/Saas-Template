from collections.abc import Iterable, Sequence
from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants.permissions import Permission
from src.dto.roles import RoleDTO
from src.infrastructure.sqlalchemy.models import role_permissions_table


async def load_permissions(session: AsyncSession, role_ids: Iterable[int]) -> dict[int, list[Permission]]:
    ids = list(role_ids)
    if not ids:
        return {}
    query = (
        sa.select(role_permissions_table.c.role_id, role_permissions_table.c.permission)
        .where(role_permissions_table.c.role_id.in_(ids))
        .order_by(role_permissions_table.c.role_id, role_permissions_table.c.permission)
    )
    result = await session.execute(query)
    permissions: dict[int, list[Permission]] = {}
    for role_id, permission in result.all():
        permissions.setdefault(role_id, []).append(Permission(permission))
    return permissions


async def build_roles(session: AsyncSession, rows: Sequence[Row[Any]]) -> list[RoleDTO]:
    """Собирает RoleDTO из строк `roles` (поля id, name, created_at), догружая права одним запросом."""
    permissions = await load_permissions(session, {row.id for row in rows})
    return [
        RoleDTO(id=row.id, name=row.name, created_at=row.created_at, permissions=permissions.get(row.id, []))
        for row in rows
    ]
