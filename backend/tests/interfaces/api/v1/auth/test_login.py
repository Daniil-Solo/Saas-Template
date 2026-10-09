from argon2 import PasswordHasher
from fastapi import status
import pytest

from src.dto.auth import UserLoginDTO
from src.infrastructure.auth.jwt import decode_access_token
from src.settings import AuthSettings
from tests.factories.users import TEST_PASSWORD
from tests.helpers.users import create_users


async def test__success(uow, api):
    user = (await create_users(uow))[0]

    token = (await api.auth.login(UserLoginDTO(email=user.email, password=TEST_PASSWORD))).validate()
    assert token.token_type == "bearer"

    auth_settings = AuthSettings()
    assert decode_access_token(token.access_token, auth_settings.secret_key, auth_settings.algorithm) == user.id


async def test__success__email_case_insensitive(uow, api):
    user = (await create_users(uow))[0]

    (await api.auth.login({"email": f"  {user.email.upper()}  ", "password": TEST_PASSWORD})).validate()


async def test__success__password_is_rehashed_when_params_outdated(uow, api):
    weak_hash = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash(TEST_PASSWORD)
    user = (await create_users(uow, hashed_password=weak_hash))[0]

    (await api.auth.login(UserLoginDTO(email=user.email, password=TEST_PASSWORD))).validate()

    async with uow.connection():
        updated = await uow.users.get_by_email(user.email)
    assert updated.hashed_password != weak_hash

    # после перехеширования вход по тому же паролю продолжает работать
    (await api.auth.login(UserLoginDTO(email=user.email, password=TEST_PASSWORD))).validate()


async def test__failed__wrong_password(uow, api):
    user = (await create_users(uow))[0]

    response = (await api.auth.login(UserLoginDTO(email=user.email, password="WrongPassword1"))).expected_error_status(
        status.HTTP_401_UNAUTHORIZED, "invalid_credentials"
    )
    assert response.headers["www-authenticate"] == "Bearer"


async def test__failed__unknown_email_same_response_as_wrong_password(uow, api):
    user = (await create_users(uow))[0]

    wrong_password = (
        await api.auth.login(UserLoginDTO(email=user.email, password="WrongPassword1"))
    ).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_credentials")
    unknown_email = (
        await api.auth.login(UserLoginDTO(email="nobody@example.com", password="WrongPassword1"))
    ).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_credentials")

    assert unknown_email.json() == wrong_password.json()


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"email": "not-an-email", "password": TEST_PASSWORD}, "email"),
        ({"email": "", "password": TEST_PASSWORD}, "email"),
        ({"email": "test@example.com", "password": ""}, "password"),
        ({"email": "test@example.com", "password": "a" * 129}, "password"),
        ({"email": "test@example.com"}, "password"),
        ({"password": TEST_PASSWORD}, "email"),
    ],
)
async def test__failed__validation(container, api, payload, field):
    (await api.auth.login(payload)).expect_validation_error(field=field)
