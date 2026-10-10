import asyncio
import datetime

from fastapi import status

from src.constants.invitations import InvitationStatus
from src.constants.permissions import Permission
from tests.helpers.auth import make_token
from tests.helpers.organizations import add_member, create_invitation, create_organization, create_role
from tests.helpers.users import create_users


async def test__success(uow, api):
    creator, invited = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    role = await create_role(uow, [Permission.INVITATIONS_MANAGE])
    invitation, token = await create_invitation(uow, organization, creator, invited.email, [role.id])

    result = (await api.invitations.accept(token, make_token(invited.id))).validate()

    assert result.id == organization.id
    async with uow.connection():
        access = await uow.members.get_access(organization.id, invited.id)
        record = await uow.invitations.get_by_id(organization.id, invitation.id)
    assert access.permissions == {Permission.INVITATIONS_MANAGE}
    assert not access.is_creator
    assert record.status == InvitationStatus.ACCEPTED
    assert record.accepted_at is not None


async def test__success__deleted_role_is_skipped(uow, api):
    creator, invited = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    kept = await create_role(uow, [Permission.INVITATIONS_MANAGE])
    removed = await create_role(uow, [Permission.MEMBERS_MANAGE])
    _, token = await create_invitation(uow, organization, creator, invited.email, [kept.id, removed.id])
    async with uow.connection():
        await uow.roles.delete(removed.id)

    (await api.invitations.accept(token, make_token(invited.id))).validate()

    async with uow.connection():
        access = await uow.members.get_access(organization.id, invited.id)
    assert access.permissions == {Permission.INVITATIONS_MANAGE}


async def test__success__without_roles(uow, api):
    creator, invited = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    _, token = await create_invitation(uow, organization, creator, invited.email)

    (await api.invitations.accept(token, make_token(invited.id))).validate()

    async with uow.connection():
        access = await uow.members.get_access(organization.id, invited.id)
    assert access.permissions == set()


async def test__failed__already_accepted(uow, api):
    creator, invited = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    _, token = await create_invitation(uow, organization, creator, invited.email)
    user_token = make_token(invited.id)

    (await api.invitations.accept(token, user_token)).validate()

    (await api.invitations.accept(token, user_token)).expected_error_status(
        status.HTTP_409_CONFLICT, "invitation_not_pending"
    )


async def test__failed__revoked(uow, api):
    creator, invited = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    _, token = await create_invitation(uow, organization, creator, invited.email, status=InvitationStatus.REVOKED)

    (await api.invitations.accept(token, make_token(invited.id))).expected_error_status(
        status.HTTP_409_CONFLICT, "invitation_not_pending"
    )


async def test__failed__expired(uow, api):
    creator, invited = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    _, token = await create_invitation(
        uow, organization, creator, invited.email, expires_in=datetime.timedelta(minutes=-1)
    )

    (await api.invitations.accept(token, make_token(invited.id))).expected_error_status(
        status.HTTP_410_GONE, "invitation_expired"
    )
    async with uow.connection():
        members = await uow.members.list_for_organization(organization.id)
    assert len(members) == 1


async def test__failed__email_mismatch(uow, api):
    creator, invited, other = await create_users(uow, size=3)
    organization = await create_organization(uow, creator)
    _, token = await create_invitation(uow, organization, creator, invited.email)

    (await api.invitations.accept(token, make_token(other.id))).expected_error_status(
        status.HTTP_403_FORBIDDEN, "invitation_email_mismatch"
    )

    # приглашение осталось действующим, и нужный пользователь его примет
    (await api.invitations.accept(token, make_token(invited.id))).validate()


async def test__failed__already_member(uow, api):
    creator, invited = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    await add_member(uow, organization, invited)
    _, token = await create_invitation(uow, organization, creator, invited.email)

    (await api.invitations.accept(token, make_token(invited.id))).expected_error_status(
        status.HTTP_409_CONFLICT, "member_already_exists"
    )


async def test__failed__not_found(uow, api):
    user = (await create_users(uow))[0]

    (await api.invitations.accept("unknown-token", make_token(user.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "invitation_not_found"
    )


async def test__failed__no_authorization_header(container, api):
    (await api.invitations.accept("token")).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")


async def test__concurrent_accept_creates_single_member(uow, api):
    creator, invited = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    _, token = await create_invitation(uow, organization, creator, invited.email)
    user_token = make_token(invited.id)

    responses = await asyncio.gather(*(api.invitations.accept(token, user_token) for _ in range(5)))

    assert sorted(r.status_code for r in responses) == [200, 409, 409, 409, 409]
    async with uow.connection():
        members = await uow.members.list_for_organization(organization.id)
    assert len(members) == 2
