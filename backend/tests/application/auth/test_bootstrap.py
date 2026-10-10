import pytest

from src.application.auth import bootstrap
from src.application.exceptions import UserNotFoundError
from src.dto.auth import UserLoginDTO
from src.settings import AdminSettings
from tests.helpers.users import create_users


async def test__success__creates_admin(container, uow, api):
    settings = AdminSettings(email="Admin@Example.com", password="admin-password-1")

    with container.admin_settings.override(settings):
        await bootstrap.ensure_admin()

    async with uow.connection():
        user = await uow.users.get_by_email("admin@example.com")
    assert user.is_admin
    assert user.is_verified
    (await api.auth.login(UserLoginDTO(email="admin@example.com", password="admin-password-1"))).validate()


async def test__success__idempotent(container, uow):
    settings = AdminSettings(email="admin@example.com", password="admin-password-1")

    with container.admin_settings.override(settings):
        await bootstrap.ensure_admin()
        await bootstrap.ensure_admin()

    async with uow.connection():
        assert (await uow.users.get_by_email("admin@example.com")).is_admin


async def test__success__existing_user_is_not_changed(container, uow):
    user = (await create_users(uow))[0]
    async with uow.connection():
        before = await uow.users.get_by_email(user.email)
    settings = AdminSettings(email=user.email, password="admin-password-1")

    with container.admin_settings.override(settings):
        await bootstrap.ensure_admin()

    async with uow.connection():
        same = await uow.users.get_by_email(user.email)
    assert not same.is_admin
    assert same.fullname == user.fullname
    assert same.hashed_password == before.hashed_password


async def test__success__not_configured_creates_nothing(container, uow):
    with container.admin_settings.override(AdminSettings(email=None, password=None)):
        await bootstrap.ensure_admin()

    async with uow.connection():
        with pytest.raises(UserNotFoundError):
            await uow.users.get_by_email("admin@example.com")


def test__settings__email_without_password():
    with pytest.raises(ValueError, match="только вместе"):
        AdminSettings(email="admin@example.com", password=None)


def test__settings__short_password():
    with pytest.raises(ValueError, match="at least 8"):
        AdminSettings(email="admin@example.com", password="short")
