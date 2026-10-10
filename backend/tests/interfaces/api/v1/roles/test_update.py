from fastapi import status

from src.constants.permissions import Permission
from src.dto.roles import RoleUpdateDTO
from tests.helpers.auth import make_token
from tests.helpers.organizations import add_member, create_organization, create_role
from tests.helpers.users import create_users


async def test__success__name_and_permissions(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]
    role = await create_role(uow, [Permission.MEMBERS_MANAGE])

    result = (
        await api.roles.update(
            role.id,
            RoleUpdateDTO(name="Renamed", permissions=[Permission.INVITATIONS_MANAGE]),
            make_token(admin.id),
        )
    ).validate()

    assert result.name == "Renamed"
    assert result.permissions == [Permission.INVITATIONS_MANAGE]


async def test__success__only_name_keeps_permissions(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]
    role = await create_role(uow, [Permission.MEMBERS_MANAGE])

    result = (await api.roles.update(role.id, {"name": "Renamed"}, make_token(admin.id))).validate()

    assert result.permissions == [Permission.MEMBERS_MANAGE]


async def test__success__empty_permissions_clear_role(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]
    role = await create_role(uow, [Permission.MEMBERS_MANAGE])

    result = (await api.roles.update(role.id, {"permissions": []}, make_token(admin.id))).validate()

    assert result.permissions == []


async def test__success__same_name_for_itself(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]
    role = await create_role(uow)

    (await api.roles.update(role.id, {"name": role.name}, make_token(admin.id))).validate()


async def test__success__permissions_change_takes_effect_immediately(uow, api):
    admin, creator, member = await create_users(uow, size=3, is_admin=True)
    organization = await create_organization(uow, creator)
    role = await create_role(uow, [Permission.MEMBERS_MANAGE])
    await add_member(uow, organization, member, [role.id])

    (await api.roles.update(role.id, {"permissions": [Permission.INVITATIONS_MANAGE]}, make_token(admin.id))).validate()

    result = (await api.organizations.get(organization.id, make_token(member.id))).validate()
    assert result.permissions == [Permission.INVITATIONS_MANAGE]


async def test__failed__not_admin(uow, api):
    user = (await create_users(uow))[0]
    role = await create_role(uow)

    (await api.roles.update(role.id, {"name": "New"}, make_token(user.id))).expected_error_status(
        status.HTTP_403_FORBIDDEN, "admin_required"
    )


async def test__failed__not_found(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]

    (await api.roles.update(9999, {"name": "New"}, make_token(admin.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "role_not_found"
    )


async def test__failed__name_exists(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]
    first = await create_role(uow)
    second = await create_role(uow)

    (await api.roles.update(second.id, {"name": first.name}, make_token(admin.id))).expected_error_status(
        status.HTTP_409_CONFLICT, "role_name_exists"
    )


async def test__failed__unknown_permission(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]
    role = await create_role(uow)

    (await api.roles.update(role.id, {"permissions": ["unknown:perm"]}, make_token(admin.id))).expect_validation_error()


async def test__failed__empty_name(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]
    role = await create_role(uow)

    (await api.roles.update(role.id, {"name": ""}, make_token(admin.id))).expect_validation_error(field="name")


async def test__failed__no_authorization_header(container, api):
    (await api.roles.update(1, {"name": "New"})).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
