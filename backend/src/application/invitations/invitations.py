import datetime

from dependency_injector.wiring import Provide, inject

from src.application.exceptions import (
    InvitationEmailMismatchError,
    InvitationExpiredError,
    InvitationNotPendingError,
    MemberAlreadyExistsError,
    RoleNotFoundError,
)
from src.constants.invitations import InvitationDisplayStatus, InvitationStatus
from src.constants.tasks import TaskName
from src.di.container import Container
from src.dto.common import SuccessOperationDTO
from src.dto.invitations import (
    InvitationCreatedDTO,
    InvitationCreateDTO,
    InvitationDTO,
    InvitationPreviewDTO,
    InvitationRecordDTO,
)
from src.dto.organizations import OrganizationAccessDTO, OrganizationDTO
from src.dto.roles import RoleDTO
from src.dto.tasks import SendInvitationEmailDTO
from src.dto.users import UserDTO
from src.infrastructure.auth import invitation_token
from src.infrastructure.queue.interface import TaskQueue
from src.infrastructure.sqlalchemy.uow import UnitOfWork
from src.settings import InvitationSettings


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def _display_status(record: InvitationRecordDTO, now: datetime.datetime) -> InvitationDisplayStatus:
    if record.status == InvitationStatus.ACCEPTED:
        return InvitationDisplayStatus.ACCEPTED
    if record.status == InvitationStatus.REVOKED:
        return InvitationDisplayStatus.REVOKED
    if record.expires_at <= now:
        return InvitationDisplayStatus.EXPIRED
    return InvitationDisplayStatus.ACTIVE


def _to_dto(record: InvitationRecordDTO, roles: list[RoleDTO], now: datetime.datetime) -> InvitationDTO:
    return InvitationDTO(
        id=record.id,
        organization_id=record.organization_id,
        email=record.email,
        status=_display_status(record, now),
        roles=roles,
        expires_at=record.expires_at,
        invited_by_id=record.invited_by_id,
        created_at=record.created_at,
        accepted_at=record.accepted_at,
    )


@inject
async def create(
    data: InvitationCreateDTO,
    access: OrganizationAccessDTO,
    uow: UnitOfWork = Provide[Container.uow],
    settings: InvitationSettings = Provide[Container.invitation_settings],
    queue: TaskQueue = Provide[Container.task_queue],
) -> InvitationCreatedDTO:
    now = _now()
    role_ids = sorted(set(data.role_ids))
    token = invitation_token.generate_token()
    async with uow.connection() as conn, conn.transaction():
        if await uow.members.exists_by_email(access.organization_id, data.email):
            raise MemberAlreadyExistsError
        roles = await uow.roles.list_by_ids(role_ids)
        if len(roles) != len(role_ids):
            raise RoleNotFoundError
        await uow.invitations.revoke_expired_pending(access.organization_id, data.email, now)
        record = await uow.invitations.create(
            organization_id=access.organization_id,
            email=data.email,
            token_hash=invitation_token.hash_token(token),
            expires_at=now + datetime.timedelta(days=settings.ttl_days),
            invited_by_id=access.user_id,
            role_ids=role_ids,
        )
    # После коммита: воркер должен найти приглашение. Токен идёт в payload - в БД только его хеш
    await queue.enqueue(
        TaskName.SEND_INVITATION_EMAIL,
        SendInvitationEmailDTO(invitation_id=record.id, token=token),
        job_id=f"invitation-{record.id}",
    )
    return InvitationCreatedDTO(**_to_dto(record, roles, now).model_dump(), token=token)


@inject
async def get_all(
    access: OrganizationAccessDTO,
    uow: UnitOfWork = Provide[Container.uow],
) -> list[InvitationDTO]:
    now = _now()
    async with uow.connection():
        records = await uow.invitations.list_for_organization(access.organization_id)
        roles = await uow.invitations.get_roles([record.id for record in records])
    return [_to_dto(record, roles.get(record.id, []), now) for record in records]


@inject
async def revoke(
    invitation_id: int,
    access: OrganizationAccessDTO,
    uow: UnitOfWork = Provide[Container.uow],
) -> SuccessOperationDTO:
    async with uow.connection():
        record = await uow.invitations.get_by_id(access.organization_id, invitation_id)
        if record.status != InvitationStatus.PENDING:
            raise InvitationNotPendingError
        await uow.invitations.mark_revoked(invitation_id)
    return SuccessOperationDTO()


@inject
async def preview(
    token: str,
    uow: UnitOfWork = Provide[Container.uow],
) -> InvitationPreviewDTO:
    now = _now()
    async with uow.connection():
        record = await uow.invitations.get_by_token_hash(invitation_token.hash_token(token))
        organization = await uow.organizations.get_by_id(record.organization_id)
        roles = (await uow.invitations.get_roles([record.id])).get(record.id, [])
    return InvitationPreviewDTO(
        organization_id=organization.id,
        organization_name=organization.name,
        email=record.email,
        status=_display_status(record, now),
        roles=roles,
        expires_at=record.expires_at,
    )


@inject
async def accept(
    token: str,
    user: UserDTO,
    uow: UnitOfWork = Provide[Container.uow],
) -> OrganizationDTO:
    now = _now()
    async with uow.connection() as conn, conn.transaction():
        # Блокировка строки: два параллельных принятия не создадут двух участников
        record = await uow.invitations.get_by_token_hash(invitation_token.hash_token(token), for_update=True)
        if record.status != InvitationStatus.PENDING:
            raise InvitationNotPendingError
        if record.expires_at <= now:
            raise InvitationExpiredError
        if record.email != user.email.strip().lower():
            raise InvitationEmailMismatchError
        member_id = await uow.members.create(record.organization_id, user.id)
        # Роли, удалённые до принятия, уже исчезли из invitation_roles (CASCADE)
        await uow.members.set_roles(member_id, await uow.invitations.get_role_ids(record.id))
        await uow.invitations.mark_accepted(record.id, now)
        return await uow.organizations.get_by_id(record.organization_id)
