from fastapi import status

from src.constants.permissions import Permission
from tests.helpers.auth import make_token
from tests.helpers.organizations import add_member, create_organization, create_role
from tests.helpers.users import create_users


async def test__success(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    role = await create_role(uow, [Permission.INVITATIONS_MANAGE])
    await add_member(uow, organization, member, [role.id])

    # список доступен любому участнику, даже без прав
    response = await api.organizations.list_members(organization.id, make_token(member.id))
    assert "hashed_password" not in response.response.text
    result = response.validate()

    assert [item.user.id for item in result] == [creator.id, member.id]
    assert result[0].is_creator
    assert result[0].roles == []
    assert not result[1].is_creator
    assert [(r.id, r.permissions) for r in result[1].roles] == [(role.id, [Permission.INVITATIONS_MANAGE])]


async def test__success__other_organizations_not_included(uow, api):
    first_creator, second_creator = await create_users(uow, size=2)
    organization = await create_organization(uow, first_creator)
    await create_organization(uow, second_creator)

    result = (await api.organizations.list_members(organization.id, make_token(first_creator.id))).validate()

    assert len(result) == 1


async def test__failed__not_a_member(uow, api):
    creator, stranger = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)

    (await api.organizations.list_members(organization.id, make_token(stranger.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "organization_not_found"
    )


async def test__failed__no_authorization_header(container, api):
    (await api.organizations.list_members(1)).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
