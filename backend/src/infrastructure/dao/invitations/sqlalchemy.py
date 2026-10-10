import datetime

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import InvitationAlreadyExistsError, InvitationNotFoundError
from src.constants.invitations import InvitationStatus
from src.dto.invitations import InvitationRecordDTO
from src.dto.roles import RoleDTO
from src.infrastructure.dao.invitations.interface import InvitationsDAO
from src.infrastructure.dao.roles.helpers import build_roles
from src.infrastructure.sqlalchemy.models import invitation_roles_table, invitations_table, roles_table

PENDING_UNIQUE_INDEX = "uq_invitations_pending_organization_email"
RECORD_COLUMNS = (
    invitations_table.c.id,
    invitations_table.c.organization_id,
    invitations_table.c.email,
    invitations_table.c.status,
    invitations_table.c.expires_at,
    invitations_table.c.invited_by_id,
    invitations_table.c.created_at,
    invitations_table.c.accepted_at,
)


class SQLAlchemyInvitationsDAO(InvitationsDAO):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        organization_id: int,
        email: str,
        token_hash: str,
        expires_at: datetime.datetime,
        invited_by_id: int,
        role_ids: list[int],
    ) -> InvitationRecordDTO:
        query = (
            sa.insert(invitations_table)
            .values(
                organization_id=organization_id,
                email=email,
                token_hash=token_hash,
                status=InvitationStatus.PENDING,
                expires_at=expires_at,
                invited_by_id=invited_by_id,
            )
            .returning(*RECORD_COLUMNS)
        )
        try:
            # SAVEPOINT: нарушение индекса не должно ломать внешнюю транзакцию
            async with self.session.begin_nested():
                result = await self.session.execute(query)
        except IntegrityError as exc:
            if PENDING_UNIQUE_INDEX in str(exc.orig):
                raise InvitationAlreadyExistsError from exc
            raise
        record = InvitationRecordDTO.model_validate(result.one())
        unique_ids = sorted(set(role_ids))
        if unique_ids:
            await self.session.execute(
                sa.insert(invitation_roles_table),
                [{"invitation_id": record.id, "role_id": role_id} for role_id in unique_ids],
            )
        return record

    async def get_by_id(self, organization_id: int, invitation_id: int) -> InvitationRecordDTO:
        query = sa.select(*RECORD_COLUMNS).where(
            invitations_table.c.id == invitation_id,
            invitations_table.c.organization_id == organization_id,
        )
        row = (await self.session.execute(query)).one_or_none()
        if row is None:
            raise InvitationNotFoundError
        return InvitationRecordDTO.model_validate(row)

    async def get_by_token_hash(self, token_hash: str, for_update: bool = False) -> InvitationRecordDTO:
        query = sa.select(*RECORD_COLUMNS).where(invitations_table.c.token_hash == token_hash)
        if for_update:
            query = query.with_for_update()
        row = (await self.session.execute(query)).one_or_none()
        if row is None:
            raise InvitationNotFoundError
        return InvitationRecordDTO.model_validate(row)

    async def list_for_organization(self, organization_id: int) -> list[InvitationRecordDTO]:
        query = (
            sa.select(*RECORD_COLUMNS)
            .where(invitations_table.c.organization_id == organization_id)
            .order_by(invitations_table.c.id.desc())
        )
        result = await self.session.execute(query)
        return [InvitationRecordDTO.model_validate(row) for row in result.all()]

    async def get_roles(self, invitation_ids: list[int]) -> dict[int, list[RoleDTO]]:
        if not invitation_ids:
            return {}
        query = (
            sa.select(roles_table, invitation_roles_table.c.invitation_id)
            .join(invitation_roles_table, invitation_roles_table.c.role_id == roles_table.c.id)
            .where(invitation_roles_table.c.invitation_id.in_(invitation_ids))
            .order_by(roles_table.c.id)
        )
        rows = (await self.session.execute(query)).all()
        roles = await build_roles(self.session, rows)
        by_invitation: dict[int, list[RoleDTO]] = {}
        for row, role in zip(rows, roles, strict=True):
            by_invitation.setdefault(row.invitation_id, []).append(role)
        return by_invitation

    async def get_role_ids(self, invitation_id: int) -> list[int]:
        query = sa.select(invitation_roles_table.c.role_id).where(
            invitation_roles_table.c.invitation_id == invitation_id
        )
        return list((await self.session.execute(query)).scalars())

    async def revoke_expired_pending(self, organization_id: int, email: str, now: datetime.datetime) -> None:
        query = (
            sa.update(invitations_table)
            .where(
                invitations_table.c.organization_id == organization_id,
                invitations_table.c.email == email,
                invitations_table.c.status == InvitationStatus.PENDING,
                invitations_table.c.expires_at <= now,
            )
            .values(status=InvitationStatus.REVOKED)
        )
        await self.session.execute(query)

    async def mark_revoked(self, invitation_id: int) -> None:
        query = (
            sa.update(invitations_table)
            .where(invitations_table.c.id == invitation_id)
            .values(status=InvitationStatus.REVOKED)
        )
        await self.session.execute(query)

    async def mark_accepted(self, invitation_id: int, accepted_at: datetime.datetime) -> None:
        query = (
            sa.update(invitations_table)
            .where(invitations_table.c.id == invitation_id)
            .values(status=InvitationStatus.ACCEPTED, accepted_at=accepted_at)
        )
        await self.session.execute(query)
