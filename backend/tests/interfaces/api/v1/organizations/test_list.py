from fastapi import status

from tests.helpers.auth import make_token
from tests.helpers.organizations import add_member, create_organization
from tests.helpers.users import create_users


async def test__success(uow, api):
    user, other = await create_users(uow, size=2)
    own = await create_organization(uow, user)
    joined = await create_organization(uow, other)
    await add_member(uow, joined, user)
    await create_organization(uow, other)  # чужая, где user не участник

    result = (await api.organizations.get_all(make_token(user.id))).validate()

    assert [organization.id for organization in result] == [own.id, joined.id]


async def test__success__empty(uow, api):
    user = (await create_users(uow))[0]

    assert (await api.organizations.get_all(make_token(user.id))).validate() == []


async def test__failed__no_authorization_header(container, api):
    (await api.organizations.get_all()).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
