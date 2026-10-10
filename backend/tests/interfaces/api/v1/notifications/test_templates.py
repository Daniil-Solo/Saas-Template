from fastapi import status

from src.constants.emails import EmailTemplate
from tests.helpers.auth import make_token
from tests.helpers.users import create_users


async def test__success(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]

    result = (await api.notifications.templates(make_token(admin.id))).validate()

    assert {item.template for item in result} == set(EmailTemplate)
    welcome = next(item for item in result if item.template == EmailTemplate.WELCOME)
    assert set(welcome.payload_schema["properties"]) == {"fullname", "login_url"}


async def test__failed__no_token(container, api):
    (await api.notifications.templates()).expected_error_status(status.HTTP_401_UNAUTHORIZED)


async def test__failed__not_admin(uow, api):
    user = (await create_users(uow))[0]

    (await api.notifications.templates(make_token(user.id))).expected_error_status(
        status.HTTP_403_FORBIDDEN, "admin_required"
    )
