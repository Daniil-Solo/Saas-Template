from fastapi import status

from src.constants.permissions import Permission
from tests.helpers.auth import make_token
from tests.helpers.users import create_users


async def test__success(uow, api):
    user = (await create_users(uow))[0]

    result = (await api.permissions.get_all(make_token(user.id))).validate()

    assert result == list(Permission)


async def test__failed__no_authorization_header(container, api):
    (await api.permissions.get_all()).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
