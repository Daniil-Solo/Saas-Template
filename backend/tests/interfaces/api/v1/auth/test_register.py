import asyncio

from fastapi import status
import pytest

from src.constants.emails import EmailTemplate
from src.constants.tasks import TaskName
from src.dto.auth import UserLoginDTO
from src.infrastructure.auth.jwt import decode_access_token
from src.settings import get_settings
from tests.factories.users import TEST_PASSWORD, UserRegisterFactory
from tests.helpers.users import create_users


async def test__success(uow, api):
    data = UserRegisterFactory.build()

    token = (await api.auth.register(data)).validate()
    assert token.token_type == "bearer"

    auth_settings = get_settings().auth
    user_id = decode_access_token(token.access_token, auth_settings.secret_key, auth_settings.algorithm)
    async with uow.connection():
        user = await uow.users.get_by_email(data.email)
    assert user.id == user_id
    assert user.fullname == data.fullname
    assert user.is_verified
    assert not user.is_admin
    # пароль хранится только в виде хеша
    assert user.hashed_password != data.password
    assert user.hashed_password.startswith("$argon2")


async def test__success__email_is_normalized(uow, api):
    data = UserRegisterFactory.build(email="  Mixed.Case@Example.COM ")

    (await api.auth.register(data)).validate()

    async with uow.connection():
        user = await uow.users.get_by_email("mixed.case@example.com")
    assert user.email == "mixed.case@example.com"

    (await api.auth.login(UserLoginDTO(email="MIXED.CASE@example.com", password=TEST_PASSWORD))).validate()


async def test__failed__duplicated_email(uow, api):
    created_user = (await create_users(uow))[0]
    data = UserRegisterFactory.build(email=created_user.email)

    (await api.auth.register(data)).expected_error_status(status.HTTP_409_CONFLICT, "user_email_exists")


async def test__failed__duplicated_email_other_case(uow, api):
    created_user = (await create_users(uow))[0]
    data = UserRegisterFactory.build(email=created_user.email.upper())

    (await api.auth.register(data)).expected_error_status(status.HTTP_409_CONFLICT, "user_email_exists")


async def test__failed__parallel_registration_same_email(uow, api):
    data = UserRegisterFactory.build()

    responses = await asyncio.gather(*(api.auth.register(data) for _ in range(5)))

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [status.HTTP_200_OK] + [status.HTTP_409_CONFLICT] * 4
    async with uow.connection():
        user = await uow.users.get_by_email(data.email)
    assert user.email == data.email


@pytest.mark.parametrize(
    ("overrides", "field", "message"),
    [
        ({"password": "short"}, "password", "at least 8 characters"),
        ({"password": "a" * 7}, "password", "at least 8 characters"),
        ({"password": "a" * 129}, "password", "at most 128 characters"),
        ({"email": "not-an-email"}, "email", None),
        ({"email": ""}, "email", None),
        ({"fullname": ""}, "fullname", "at least 1 character"),
        ({"fullname": "a" * 256}, "fullname", "at most 255 characters"),
    ],
)
async def test__failed__validation(container, api, overrides, field, message):
    payload = {"fullname": "Test User", "email": "test@example.com", "password": TEST_PASSWORD} | overrides

    (await api.auth.register(payload)).expect_validation_error(message, field=field)


@pytest.mark.parametrize("missing_field", ["fullname", "email", "password"])
async def test__failed__missing_field(container, api, missing_field):
    payload = {"fullname": "Test User", "email": "test@example.com", "password": TEST_PASSWORD}
    del payload[missing_field]

    (await api.auth.register(payload)).expect_validation_error("Field required", field=missing_field)


@pytest.mark.parametrize("length", [8, 128])
async def test__success__boundary_password_lengths(container, api, length):
    payload = {"fullname": "Test User", "email": f"boundary{length}@example.com", "password": "a" * length}

    (await api.auth.register(payload)).validate()


async def test__success__welcome_email_is_enqueued(uow, api, task_queue):
    data = UserRegisterFactory.build()

    (await api.auth.register(data)).validate()

    async with uow.connection():
        user = await uow.users.get_by_email(data.email)
    assert len(task_queue.tasks) == 1
    task = task_queue.tasks[0]
    assert task.task == TaskName.SEND_EMAIL
    assert task.job_id == f"welcome-{user.id}"
    assert task.payload.to == user.email
    assert task.payload.template == EmailTemplate.WELCOME
    assert task.payload.context["fullname"] == data.fullname
    assert task.payload.context["login_url"].endswith("/login")


async def test__failed__duplicated_email_enqueues_nothing(uow, api, task_queue):
    created_user = (await create_users(uow))[0]

    (await api.auth.register(UserRegisterFactory.build(email=created_user.email))).expected_error_status(
        status.HTTP_409_CONFLICT, "user_email_exists"
    )

    assert task_queue.tasks == []
