from fastapi import status

from src.constants.permissions import Permission
from tests.factories.organizations import OrganizationCreateFactory
from tests.helpers.auth import make_token
from tests.helpers.users import create_users


async def test__success(uow, api):
    user = (await create_users(uow))[0]
    data = OrganizationCreateFactory.build()

    organization = (await api.organizations.create(data, make_token(user.id))).validate()

    assert organization.name == data.name
    assert organization.created_by_id == user.id
    async with uow.connection():
        access = await uow.members.get_access(organization.id, user.id)
    # создатель стал участником без ролей, но проходит любую проверку права
    assert access.is_creator
    assert access.permissions == set(Permission)
    async with uow.connection():
        members = await uow.members.list_for_organization(organization.id)
    assert len(members) == 1
    assert members[0].roles == []


async def test__success__same_name_allowed(uow, api):
    user = (await create_users(uow))[0]
    data = OrganizationCreateFactory.build()
    token = make_token(user.id)

    first = (await api.organizations.create(data, token)).validate()
    second = (await api.organizations.create(data, token)).validate()

    assert first.id != second.id


async def test__failed__no_authorization_header(container, api):
    data = OrganizationCreateFactory.build()

    (await api.organizations.create(data)).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")


async def test__failed__empty_name(uow, api):
    user = (await create_users(uow))[0]

    (await api.organizations.create({"name": ""}, make_token(user.id))).expect_validation_error(field="name")


async def test__failed__too_long_name(uow, api):
    user = (await create_users(uow))[0]

    (await api.organizations.create({"name": "a" * 256}, make_token(user.id))).expect_validation_error(field="name")


async def test__success__max_length_name(uow, api):
    user = (await create_users(uow))[0]

    organization = (await api.organizations.create({"name": "a" * 255}, make_token(user.id))).validate()

    assert len(organization.name) == 255
