import datetime

from fastapi import status

from src.constants.invitations import InvitationDisplayStatus, InvitationStatus
from src.constants.permissions import Permission
from tests.helpers.auth import make_token
from tests.helpers.organizations import add_member, create_invitation, create_organization, create_role
from tests.helpers.users import create_users


async def test__success__all_statuses(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    role = await create_role(uow)
    active, _ = await create_invitation(uow, organization, creator, "a@example.com", [role.id])
    accepted, _ = await create_invitation(uow, organization, creator, "b@example.com", status=InvitationStatus.ACCEPTED)
    revoked, _ = await create_invitation(uow, organization, creator, "c@example.com", status=InvitationStatus.REVOKED)
    expired, _ = await create_invitation(
        uow, organization, creator, "d@example.com", expires_in=datetime.timedelta(days=-1)
    )

    result = (await api.invitations.get_all(organization.id, make_token(creator.id))).validate()

    statuses = {item.id: item.status for item in result}
    assert statuses == {
        active.id: InvitationDisplayStatus.ACTIVE,
        accepted.id: InvitationDisplayStatus.ACCEPTED,
        revoked.id: InvitationDisplayStatus.REVOKED,
        expired.id: InvitationDisplayStatus.EXPIRED,
    }
    assert [item.id for item in result] == sorted(statuses, reverse=True)
    assert [r.id for item in result if item.id == active.id for r in item.roles] == [role.id]


async def test__success__token_is_not_exposed(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    await create_invitation(uow, organization, creator, "a@example.com")

    response = await api.invitations.get_all(organization.id, make_token(creator.id))

    assert "token" not in response.json()[0]


async def test__success__only_own_organization(uow, api):
    creator, other_creator = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    other_organization = await create_organization(uow, other_creator)
    await create_invitation(uow, other_organization, other_creator, "a@example.com")

    assert (await api.invitations.get_all(organization.id, make_token(creator.id))).validate() == []


async def test__failed__no_permission(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    role = await create_role(uow, [Permission.MEMBERS_MANAGE])
    await add_member(uow, organization, member, [role.id])

    (await api.invitations.get_all(organization.id, make_token(member.id))).expected_error_status(
        status.HTTP_403_FORBIDDEN, "permission_denied"
    )


async def test__failed__not_a_member(uow, api):
    creator, stranger = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)

    (await api.invitations.get_all(organization.id, make_token(stranger.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "organization_not_found"
    )


async def test__failed__no_authorization_header(container, api):
    (await api.invitations.get_all(1)).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
