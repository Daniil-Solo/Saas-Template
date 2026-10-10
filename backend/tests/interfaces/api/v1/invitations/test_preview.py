import datetime

from fastapi import status

from src.constants.invitations import InvitationDisplayStatus, InvitationStatus
from tests.helpers.auth import make_token
from tests.helpers.organizations import create_invitation, create_organization, create_role
from tests.helpers.users import create_users


async def test__success(uow, api):
    creator, invited = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    role = await create_role(uow)
    _, token = await create_invitation(uow, organization, creator, invited.email, [role.id])

    result = (await api.invitations.preview(token, make_token(invited.id))).validate()

    assert result.organization_id == organization.id
    assert result.organization_name == organization.name
    assert result.email == invited.email
    assert result.status == InvitationDisplayStatus.ACTIVE
    assert [r.id for r in result.roles] == [role.id]


async def test__success__any_statuses_are_shown(uow, api):
    creator, invited = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    _, expired_token = await create_invitation(
        uow, organization, creator, "a@example.com", expires_in=datetime.timedelta(days=-1)
    )
    _, revoked_token = await create_invitation(
        uow, organization, creator, "b@example.com", status=InvitationStatus.REVOKED
    )
    token = make_token(invited.id)

    assert (await api.invitations.preview(expired_token, token)).validate().status == InvitationDisplayStatus.EXPIRED
    assert (await api.invitations.preview(revoked_token, token)).validate().status == InvitationDisplayStatus.REVOKED


async def test__success__deleted_role_is_not_shown(uow, api):
    creator, invited = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    role = await create_role(uow)
    _, token = await create_invitation(uow, organization, creator, invited.email, [role.id])
    async with uow.connection():
        await uow.roles.delete(role.id)

    result = (await api.invitations.preview(token, make_token(invited.id))).validate()

    assert result.roles == []


async def test__failed__not_found(uow, api):
    user = (await create_users(uow))[0]

    (await api.invitations.preview("unknown-token", make_token(user.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "invitation_not_found"
    )


async def test__failed__no_authorization_header(container, api):
    (await api.invitations.preview("token")).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
