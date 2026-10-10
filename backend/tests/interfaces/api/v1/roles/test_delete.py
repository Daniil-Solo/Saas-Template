from fastapi import status

from src.constants.permissions import Permission
from tests.helpers.auth import make_token
from tests.helpers.organizations import add_member, create_invitation, create_organization, create_role
from tests.helpers.users import create_users


async def test__success(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]
    role = await create_role(uow)

    (await api.roles.delete(role.id, make_token(admin.id))).validate()

    assert (await api.roles.get_all(make_token(admin.id))).validate() == []


async def test__success__role_removed_from_members_and_invitations(uow, api):
    admin, creator, member = await create_users(uow, size=3, is_admin=True)
    organization = await create_organization(uow, creator)
    role = await create_role(uow, [Permission.MEMBERS_MANAGE])
    other_role = await create_role(uow, [Permission.INVITATIONS_MANAGE])
    member_id = await add_member(uow, organization, member, [role.id, other_role.id])
    invitation, _ = await create_invitation(uow, organization, creator, "a@example.com", [role.id])

    (await api.roles.delete(role.id, make_token(admin.id))).validate()

    members = (await api.organizations.list_members(organization.id, make_token(creator.id))).validate()
    assert [r.id for m in members if m.id == member_id for r in m.roles] == [other_role.id]
    async with uow.connection():
        assert await uow.invitations.get_role_ids(invitation.id) == []


async def test__failed__not_admin(uow, api):
    user = (await create_users(uow))[0]
    role = await create_role(uow)

    (await api.roles.delete(role.id, make_token(user.id))).expected_error_status(
        status.HTTP_403_FORBIDDEN, "admin_required"
    )


async def test__failed__not_found(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]

    (await api.roles.delete(9999, make_token(admin.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "role_not_found"
    )


async def test__failed__no_authorization_header(container, api):
    (await api.roles.delete(1)).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
