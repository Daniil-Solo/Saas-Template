from fastapi import status

from src.constants.permissions import Permission
from tests.helpers.auth import make_token
from tests.helpers.organizations import create_role
from tests.helpers.users import create_users


async def test__success(uow, api):
    user = (await create_users(uow))[0]  # не админ: список ролей доступен любому пользователю
    first = await create_role(uow, [Permission.MEMBERS_MANAGE, Permission.INVITATIONS_MANAGE])
    second = await create_role(uow, [])

    result = (await api.roles.get_all(make_token(user.id))).validate()

    assert [role.id for role in result] == [first.id, second.id]
    assert result[0].permissions == [Permission.INVITATIONS_MANAGE, Permission.MEMBERS_MANAGE]
    assert result[1].permissions == []


async def test__success__empty(uow, api):
    user = (await create_users(uow))[0]

    assert (await api.roles.get_all(make_token(user.id))).validate() == []


async def test__failed__no_authorization_header(container, api):
    (await api.roles.get_all()).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
