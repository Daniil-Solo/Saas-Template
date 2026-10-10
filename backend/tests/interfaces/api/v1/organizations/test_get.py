from fastapi import status

from src.constants.permissions import Permission
from tests.helpers.auth import make_token
from tests.helpers.organizations import add_member, create_organization, create_role
from tests.helpers.users import create_users


async def test__success__creator(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)

    result = (await api.organizations.get(organization.id, make_token(creator.id))).validate()

    assert result.id == organization.id
    assert result.is_creator
    assert set(result.permissions) == set(Permission)


async def test__success__member_permissions_are_union_of_roles(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    first = await create_role(uow, [Permission.MEMBERS_MANAGE])
    second = await create_role(uow, [Permission.INVITATIONS_MANAGE, Permission.MEMBERS_MANAGE])
    await add_member(uow, organization, member, [first.id, second.id])

    result = (await api.organizations.get(organization.id, make_token(member.id))).validate()

    assert not result.is_creator
    assert sorted(result.permissions) == sorted(Permission)


async def test__success__member_without_roles_has_no_permissions(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    await add_member(uow, organization, member)

    result = (await api.organizations.get(organization.id, make_token(member.id))).validate()

    assert result.permissions == []
    assert not result.is_creator


async def test__failed__not_a_member(uow, api):
    creator, stranger = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)

    (await api.organizations.get(organization.id, make_token(stranger.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "organization_not_found"
    )


async def test__failed__organization_does_not_exist(uow, api):
    user = (await create_users(uow))[0]

    (await api.organizations.get(9999, make_token(user.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "organization_not_found"
    )


async def test__failed__no_authorization_header(container, api):
    (await api.organizations.get(1)).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
