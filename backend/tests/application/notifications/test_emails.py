import datetime

import pytest
import structlog

from src.application.notifications import emails as emails_service
from src.constants.emails import EmailTemplate
from src.constants.invitations import InvitationStatus
from src.dto.emails import WelcomeEmailContext
from src.interfaces.api.app import create_app
from tests.helpers.organizations import create_invitation, create_organization, create_role
from tests.helpers.users import create_users


async def test__send__renders_and_sends(container, email_sender):
    context = WelcomeEmailContext(fullname="Анна", login_url="http://localhost/login")

    await emails_service.send("a@example.com", EmailTemplate.WELCOME, context)

    message = email_sender.messages[0]
    assert message.to == "a@example.com"
    assert "Анна" in message.html
    assert "http://localhost/login" in message.text


async def test__send_invitation__success(uow, email_sender):
    inviter, _ = await create_users(uow, size=2)
    organization = await create_organization(uow, inviter, name="Ромашка")
    role = await create_role(uow)
    record, token = await create_invitation(uow, organization, inviter, "new@example.com", [role.id])

    sent = await emails_service.send_invitation(record.id, token)

    assert sent is True
    message = email_sender.messages[0]
    assert message.to == "new@example.com"
    assert "Ромашка" in message.html
    assert inviter.fullname in message.text
    assert role.name in message.text
    assert f"/invitations/{token}" in message.text


@pytest.mark.parametrize("status", [InvitationStatus.REVOKED, InvitationStatus.ACCEPTED])
async def test__send_invitation__not_pending_is_skipped(uow, email_sender, status):
    inviter = (await create_users(uow))[0]
    organization = await create_organization(uow, inviter)
    record, token = await create_invitation(uow, organization, inviter, "new@example.com", status=status)

    assert await emails_service.send_invitation(record.id, token) is False
    assert email_sender.messages == []


async def test__send_invitation__expired_is_skipped(uow, email_sender):
    inviter = (await create_users(uow))[0]
    organization = await create_organization(uow, inviter)
    record, token = await create_invitation(
        uow, organization, inviter, "new@example.com", expires_in=datetime.timedelta(seconds=-1)
    )

    assert await emails_service.send_invitation(record.id, token) is False
    assert email_sender.messages == []


async def test__send_invitation__unknown_token_is_skipped(container, email_sender):
    assert await emails_service.send_invitation(1, "unknown-token") is False
    assert email_sender.messages == []


def test__create_app_warns_about_console_backend(monkeypatch):
    # setup_logging переконфигурирует structlog и сбил бы перехват логов
    monkeypatch.setattr("src.interfaces.api.app.setup_logging", lambda settings: None)
    monkeypatch.setattr("src.interfaces.api.app.setup_sentry", lambda *args, **kwargs: None)
    with structlog.testing.capture_logs() as logs:
        create_app()

    assert any(log["event"] == "email_console_backend_enabled" and log["log_level"] == "warning" for log in logs)
