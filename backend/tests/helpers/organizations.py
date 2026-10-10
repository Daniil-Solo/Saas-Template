import datetime

from src.constants.invitations import InvitationStatus
from src.constants.permissions import Permission
from src.dto.invitations import InvitationRecordDTO
from src.dto.organizations import OrganizationDTO
from src.dto.roles import RoleCreateDTO, RoleDTO
from src.dto.users import UserDTO
from src.infrastructure.auth import invitation_token
from src.infrastructure.sqlalchemy.uow import UnitOfWork
from tests.factories.organizations import OrganizationCreateFactory, RoleCreateFactory


async def create_organization(uow: UnitOfWork, creator: UserDTO, name: str | None = None) -> OrganizationDTO:
    """Организация с создателем-участником (без ролей), как при создании через API."""
    data = OrganizationCreateFactory.build(**({"name": name} if name else {}))
    async with uow.connection():
        organization = await uow.organizations.create(data.name, creator.id)
        await uow.members.create(organization.id, creator.id)
    return organization


async def create_role(
    uow: UnitOfWork,
    permissions: list[Permission] | None = None,
    name: str | None = None,
) -> RoleDTO:
    kwargs: dict = {}
    if permissions is not None:
        kwargs["permissions"] = permissions
    if name is not None:
        kwargs["name"] = name
    data: RoleCreateDTO = RoleCreateFactory.build(**kwargs)
    async with uow.connection():
        return await uow.roles.create(data)


async def add_member(
    uow: UnitOfWork,
    organization: OrganizationDTO,
    user: UserDTO,
    role_ids: list[int] | None = None,
) -> int:
    """Добавляет пользователя в организацию, возвращает id участника."""
    async with uow.connection():
        member_id = await uow.members.create(organization.id, user.id)
        if role_ids:
            await uow.members.set_roles(member_id, role_ids)
    return member_id


async def create_invitation(
    uow: UnitOfWork,
    organization: OrganizationDTO,
    invited_by: UserDTO,
    email: str,
    role_ids: list[int] | None = None,
    expires_in: datetime.timedelta = datetime.timedelta(days=7),
    status: InvitationStatus = InvitationStatus.PENDING,
) -> tuple[InvitationRecordDTO, str]:
    """Приглашение напрямую в БД; возвращает запись и открытый токен."""
    token = invitation_token.generate_token()
    async with uow.connection():
        record = await uow.invitations.create(
            organization_id=organization.id,
            email=email,
            token_hash=invitation_token.hash_token(token),
            expires_at=datetime.datetime.now(datetime.UTC) + expires_in,
            invited_by_id=invited_by.id,
            role_ids=role_ids or [],
        )
        if status == InvitationStatus.REVOKED:
            await uow.invitations.mark_revoked(record.id)
        elif status == InvitationStatus.ACCEPTED:
            await uow.invitations.mark_accepted(record.id, datetime.datetime.now(datetime.UTC))
    return record, token
