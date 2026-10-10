from arq import Retry
import pytest
import structlog

from src.constants.emails import EmailTemplate
from src.infrastructure.email_sender.exceptions import EmailPermanentError, EmailTemporaryError
from src.interfaces.tasks.emails import MAX_TRIES, retry_delay, send_email, send_invitation_email
from tests.helpers.organizations import create_invitation, create_organization
from tests.helpers.users import create_users

WELCOME_PAYLOAD = {
    "to": "a@example.com",
    "template": EmailTemplate.WELCOME.value,
    "context": {"fullname": "Анна", "login_url": "http://localhost/login"},
}


def test__retry_delay_grows():
    assert [retry_delay(attempt) for attempt in (1, 2, 3, 4)] == [30, 120, 270, 480]


async def test__send_email__success(container, email_sender):
    await send_email({"job_try": 1, "job_id": "j"}, WELCOME_PAYLOAD)

    assert email_sender.messages[0].to == "a@example.com"


async def test__send_email__temporary_error_retries(container, email_sender):
    email_sender.error = EmailTemporaryError("boom")

    with pytest.raises(Retry) as exc_info:
        await send_email({"job_try": 2, "job_id": "j"}, WELCOME_PAYLOAD)

    assert exc_info.value.defer_score == 120 * 1000


async def test__send_email__temporary_error_on_last_try_logs_error(container, email_sender):
    email_sender.error = EmailTemporaryError("boom")

    with structlog.testing.capture_logs() as logs:
        await send_email({"job_try": MAX_TRIES, "job_id": "j"}, WELCOME_PAYLOAD)

    failed = [log for log in logs if log["event"] == "email_failed"]
    assert failed[0]["log_level"] == "error"
    assert failed[0]["attempt"] == MAX_TRIES
    assert "a@example.com" not in str(failed)


async def test__send_email__permanent_error_does_not_retry(container, email_sender):
    email_sender.error = EmailPermanentError("bad address")

    with structlog.testing.capture_logs() as logs:
        await send_email({"job_try": 1, "job_id": "j"}, WELCOME_PAYLOAD)

    assert [log["log_level"] for log in logs if log["event"] == "email_failed"] == ["error"]


async def test__send_email__invalid_context_does_not_retry(container, email_sender):
    payload = {**WELCOME_PAYLOAD, "context": {"fullname": "Анна"}}

    with structlog.testing.capture_logs() as logs:
        await send_email({"job_try": 1, "job_id": "j"}, payload)

    assert email_sender.messages == []
    assert any(log["event"] == "email_failed" and log["error"] == "invalid_payload" for log in logs)


async def test__send_invitation_email__success(uow, email_sender):
    inviter = (await create_users(uow))[0]
    organization = await create_organization(uow, inviter)
    record, token = await create_invitation(uow, organization, inviter, "new@example.com")

    await send_invitation_email({"job_try": 1}, {"invitation_id": record.id, "token": token})

    assert email_sender.messages[0].to == "new@example.com"


async def test__send_invitation_email__temporary_error_retries(uow, email_sender):
    inviter = (await create_users(uow))[0]
    organization = await create_organization(uow, inviter)
    record, token = await create_invitation(uow, organization, inviter, "new@example.com")
    email_sender.error = EmailTemporaryError("boom")

    with pytest.raises(Retry):
        await send_invitation_email({"job_try": 1}, {"invitation_id": record.id, "token": token})
