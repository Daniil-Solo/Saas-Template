import datetime

from fastapi import status
import pytest
import sqlalchemy as sa

from src.infrastructure.sqlalchemy.models import users_table
from tests.helpers.auth import encode_raw_token, make_token
from tests.helpers.users import create_users


async def test__success(uow, api):
    user = (await create_users(uow))[0]

    result = await api.users.me(make_token(user.id))
    assert result.validate() == user
    # хеш пароля никогда не отдается наружу
    assert "hashed_password" not in result.json()
    assert "password" not in result.json()


async def test__success__returns_only_token_owner(uow, api):
    first, second = await create_users(uow, size=2)

    result = (await api.users.me(make_token(second.id))).validate()
    assert result.id == second.id != first.id


async def test__failed__no_authorization_header(container, api):
    response = (await api.users.me()).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
    assert response.headers["www-authenticate"] == "Bearer"


async def test__failed__garbage_token(container, api):
    (await api.users.me("not.a.jwt")).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")


async def test__failed__wrong_auth_scheme(uow, api):
    user = (await create_users(uow))[0]

    (await api.users.me(make_token(user.id), scheme="Basic")).expected_error_status(
        status.HTTP_401_UNAUTHORIZED, "invalid_token"
    )


async def test__failed__expired_token(uow, api):
    user = (await create_users(uow))[0]
    token = make_token(user.id, ttl=datetime.timedelta(minutes=-1))

    (await api.users.me(token)).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")


async def test__failed__token_signed_with_other_secret(uow, api):
    user = (await create_users(uow))[0]
    token = make_token(user.id, secret_key="another-secret-key-0123456789abcdef")

    (await api.users.me(token)).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")


async def test__failed__alg_none_token(uow, api):
    user = (await create_users(uow))[0]
    expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
    token = encode_raw_token({"sub": str(user.id), "exp": expires_at}, algorithm="none")

    (await api.users.me(token)).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")


@pytest.mark.parametrize(
    "claims",
    [
        {"sub": "1"},  # нет exp
        {"exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)},  # нет sub
        {"sub": "abc", "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)},  # sub не число
    ],
)
async def test__failed__invalid_claims(uow, api, claims):
    await create_users(uow)

    (await api.users.me(encode_raw_token(claims))).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")


async def test__failed__user_deleted(container, uow, api):
    user = (await create_users(uow))[0]
    token = make_token(user.id)
    engine = await container.engine()
    async with engine.begin() as conn:
        await conn.execute(sa.delete(users_table).where(users_table.c.id == user.id))

    (await api.users.me(token)).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
