from fastapi import status

from src.constants.invitations import InvitationStatus
from src.constants.permissions import Permission
from tests.helpers.auth import make_token
from tests.helpers.organizations import add_member, create_invitation, create_organization, create_role
from tests.helpers.users import create_users


async def test__success(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    invitation, _ = await create_invitation(uow, organization, creator, "a@example.com")

    (await api.invitations.revoke(organization.id, invitation.id, make_token(creator.id))).validate()

    async with uow.connection():
        record = await uow.invitations.get_by_id(organization.id, invitation.id)
    assert record.status == InvitationStatus.REVOKED


async def test__success__can_invite_again_after_revoke(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    invitation, _ = await create_invitation(uow, organization, creator, "a@example.com")
    token = make_token(creator.id)

    (await api.invitations.revoke(organization.id, invitation.id, token)).validate()

    await create_invitation(uow, organization, creator, "a@example.com")


async def test__failed__already_revoked(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    invitation, _ = await create_invitation(
        uow, organization, creator, "a@example.com", status=InvitationStatus.REVOKED
    )

    (await api.invitations.revoke(organization.id, invitation.id, make_token(creator.id))).expected_error_status(
        status.HTTP_409_CONFLICT, "invitation_not_pending"
    )


async def test__failed__already_accepted(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    invitation, _ = await create_invitation(
        uow, organization, creator, "a@example.com", status=InvitationStatus.ACCEPTED
    )

    (await api.invitations.revoke(organization.id, invitation.id, make_token(creator.id))).expected_error_status(
        status.HTTP_409_CONFLICT, "invitation_not_pending"
    )


async def test__failed__not_found(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)

    (await api.invitations.revoke(organization.id, 9999, make_token(creator.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "invitation_not_found"
    )


async def test__failed__invitation_of_other_organization(uow, api):
    creator, other_creator = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    other_organization = await create_organization(uow, other_creator)
    invitation, _ = await create_invitation(uow, other_organization, other_creator, "a@example.com")

    (await api.invitations.revoke(organization.id, invitation.id, make_token(creator.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "invitation_not_found"
    )


async def test__failed__no_permission(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    role = await create_role(uow, [Permission.MEMBERS_MANAGE])
    await add_member(uow, organization, member, [role.id])
    invitation, _ = await create_invitation(uow, organization, creator, "a@example.com")

    (await api.invitations.revoke(organization.id, invitation.id, make_token(member.id))).expected_error_status(
        status.HTTP_403_FORBIDDEN, "permission_denied"
    )


async def test__failed__not_a_member(uow, api):
    creator, stranger = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    invitation, _ = await create_invitation(uow, organization, creator, "a@example.com")

    (await api.invitations.revoke(organization.id, invitation.id, make_token(stranger.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "organization_not_found"
    )


async def test__failed__no_authorization_header(container, api):
    (await api.invitations.revoke(1, 1)).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
