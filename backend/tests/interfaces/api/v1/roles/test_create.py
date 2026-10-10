from fastapi import status

from src.constants.permissions import Permission
from tests.factories.organizations import RoleCreateFactory
from tests.helpers.auth import make_token
from tests.helpers.organizations import create_role
from tests.helpers.users import create_users


async def test__success(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]
    data = RoleCreateFactory.build(permissions=[Permission.MEMBERS_MANAGE, Permission.INVITATIONS_MANAGE])

    result = (await api.roles.create(data, make_token(admin.id))).validate()

    assert result.name == data.name
    assert sorted(result.permissions) == sorted(Permission)
    async with uow.connection():
        assert await uow.roles.get_by_id(result.id) == result


async def test__success__without_permissions(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]

    result = (await api.roles.create({"name": "Empty"}, make_token(admin.id))).validate()

    assert result.permissions == []


async def test__success__duplicate_permissions_are_collapsed(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]
    payload = {"name": "Dup", "permissions": ["members:manage", "members:manage"]}

    result = (await api.roles.create(payload, make_token(admin.id))).validate()

    assert result.permissions == [Permission.MEMBERS_MANAGE]


async def test__failed__not_admin(uow, api):
    user = (await create_users(uow))[0]

    (await api.roles.create(RoleCreateFactory.build(), make_token(user.id))).expected_error_status(
        status.HTTP_403_FORBIDDEN, "admin_required"
    )


async def test__failed__name_exists(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]
    existing = await create_role(uow)

    (await api.roles.create(RoleCreateFactory.build(name=existing.name), make_token(admin.id))).expected_error_status(
        status.HTTP_409_CONFLICT, "role_name_exists"
    )


async def test__failed__unknown_permission(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]

    (
        await api.roles.create({"name": "Bad", "permissions": ["unknown:perm"]}, make_token(admin.id))
    ).expect_validation_error()


async def test__failed__empty_name(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]

    (await api.roles.create({"name": "", "permissions": []}, make_token(admin.id))).expect_validation_error(
        field="name"
    )


async def test__failed__too_long_name(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]

    (await api.roles.create({"name": "a" * 256}, make_token(admin.id))).expect_validation_error(field="name")


async def test__failed__no_authorization_header(container, api):
    (await api.roles.create(RoleCreateFactory.build())).expected_error_status(
        status.HTTP_401_UNAUTHORIZED, "invalid_token"
    )
