from fastapi import status

from src.constants.emails import EmailTemplate
from src.constants.tasks import TaskName
from tests.helpers.auth import make_token
from tests.helpers.organizations import create_organization
from tests.helpers.users import create_users

WELCOME = {"fullname": "Анна", "login_url": "http://localhost/login"}


def _body(**overrides):
    return {"template": "welcome", "to": "a@example.com", "payload": WELCOME, **overrides}


async def test__success(uow, api, task_queue):
    admin = (await create_users(uow, is_admin=True))[0]

    result = (await api.notifications.send_email(_body(), make_token(admin.id))).validate()

    assert len(task_queue.tasks) == 1
    task = task_queue.tasks[0]
    assert task.task == TaskName.SEND_EMAIL
    assert task.job_id == result.job_id
    assert task.payload.to == "a@example.com"
    assert task.payload.template == EmailTemplate.WELCOME
    assert task.payload.context == WELCOME


async def test__success__idempotency_key(uow, api, task_queue):
    admin = (await create_users(uow, is_admin=True))[0]
    token = make_token(admin.id)

    first = (await api.notifications.send_email(_body(idempotency_key="abc-1"), token)).validate()
    (await api.notifications.send_email(_body(idempotency_key="abc-1"), token)).validate()

    assert first.job_id == "email-abc-1"
    assert len(task_queue.tasks) == 1


async def test__failed__no_token(container, api, task_queue):
    (await api.notifications.send_email(_body())).expected_error_status(status.HTTP_401_UNAUTHORIZED)
    assert task_queue.tasks == []


async def test__failed__garbage_token(container, api, task_queue):
    (await api.notifications.send_email(_body(), "garbage")).expected_error_status(status.HTTP_401_UNAUTHORIZED)
    assert task_queue.tasks == []


async def test__failed__not_admin(uow, api, task_queue):
    user = (await create_users(uow))[0]

    (await api.notifications.send_email(_body(), make_token(user.id))).expected_error_status(
        status.HTTP_403_FORBIDDEN, "admin_required"
    )
    assert task_queue.tasks == []


async def test__failed__organization_creator(uow, api, task_queue):
    creator = (await create_users(uow))[0]
    await create_organization(uow, creator)

    (await api.notifications.send_email(_body(), make_token(creator.id))).expected_error_status(
        status.HTTP_403_FORBIDDEN, "admin_required"
    )
    assert task_queue.tasks == []


async def test__failed__unknown_template(uow, api, task_queue):
    admin = (await create_users(uow, is_admin=True))[0]

    (await api.notifications.send_email(_body(template="nope"), make_token(admin.id))).expect_validation_error(
        field="template"
    )
    assert task_queue.tasks == []


async def test__failed__missing_payload_field(uow, api, task_queue):
    admin = (await create_users(uow, is_admin=True))[0]

    (
        await api.notifications.send_email(_body(payload={"fullname": "Анна"}), make_token(admin.id))
    ).expect_validation_error(field="login_url")
    assert task_queue.tasks == []


async def test__failed__extra_payload_field(uow, api, task_queue):
    admin = (await create_users(uow, is_admin=True))[0]

    (
        await api.notifications.send_email(_body(payload={**WELCOME, "extra": 1}), make_token(admin.id))
    ).expect_validation_error(field="extra")
    assert task_queue.tasks == []


async def test__failed__invalid_to(uow, api, task_queue):
    admin = (await create_users(uow, is_admin=True))[0]

    (await api.notifications.send_email(_body(to="not-an-email"), make_token(admin.id))).expect_validation_error(
        field="to"
    )
    assert task_queue.tasks == []


async def test__failed__bad_idempotency_key(uow, api):
    admin = (await create_users(uow, is_admin=True))[0]

    (
        await api.notifications.send_email(_body(idempotency_key="bad key!"), make_token(admin.id))
    ).expect_validation_error(field="idempotency_key")
