from email import message_from_bytes
import socket

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import AuthResult, LoginPassword
import httpx
import pytest
import structlog

from src.dto.emails import EmailMessage
from src.infrastructure.email_sender.console import ConsoleEmailSender
from src.infrastructure.email_sender.exceptions import EmailPermanentError, EmailTemporaryError
from src.infrastructure.email_sender.maileroo import MailerooEmailSender
from src.infrastructure.email_sender.smtp import SmtpEmailSender
from src.settings import EmailSettings, MailerooSettings, SmtpSettings

MESSAGE = EmailMessage(to="to@example.com", subject="Тема", html="<p>Привет</p>", text="Привет")
EMAIL = EmailSettings(from_address="from@example.com", from_display_name="Сервис")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Collector:
    def __init__(self):
        self.envelopes = []

    async def handle_DATA(self, server, session, envelope):  # noqa: N802
        self.envelopes.append(envelope)
        return "250 OK"


@pytest.fixture
def smtp_server():
    handler = Collector()

    def authenticator(server, session, envelope, mechanism, auth_data):
        ok = isinstance(auth_data, LoginPassword) and auth_data.login == b"user" and auth_data.password == b"pass"
        return AuthResult(success=ok, handled=False)

    controller = Controller(
        handler, hostname="127.0.0.1", port=_free_port(), authenticator=authenticator, auth_require_tls=False
    )
    controller.start()
    controller.collector = handler
    yield controller
    controller.stop()


def _smtp(controller, **kwargs):
    port = controller.port
    return SmtpEmailSender(EMAIL, SmtpSettings(host="127.0.0.1", port=port, tls="none", **kwargs))


async def test__smtp__success(smtp_server):
    await _smtp(smtp_server).send(MESSAGE)

    envelope = smtp_server.collector.envelopes[0]
    assert envelope.rcpt_tos == ["to@example.com"]
    parsed = message_from_bytes(envelope.original_content)
    assert "from@example.com" in parsed["From"]
    assert parsed.is_multipart()


async def test__smtp__auth_success(smtp_server):
    await _smtp(smtp_server, username="user", password="pass").send(MESSAGE)

    assert len(smtp_server.collector.envelopes) == 1


async def test__smtp__auth_failed_is_permanent(smtp_server):
    with pytest.raises(EmailPermanentError):
        await _smtp(smtp_server, username="user", password="wrong").send(MESSAGE)


async def test__smtp__unreachable_is_temporary():
    sender = SmtpEmailSender(EMAIL, SmtpSettings(host="127.0.0.1", port=1, tls="none", timeout=2))

    with pytest.raises(EmailTemporaryError):
        await sender.send(MESSAGE)


def _maileroo(handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return MailerooEmailSender(EMAIL, MailerooSettings(api_key="key"), client=client)


async def test__maileroo__success():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["headers"] = request.headers
        seen["body"] = request.read()
        return httpx.Response(200, json={"success": True})

    await _maileroo(handler).send(MESSAGE)

    assert seen["headers"]["x-api-key"] == "key"
    assert b"to@example.com" in seen["body"]


@pytest.mark.parametrize(
    ("status_code", "error"),
    [
        (400, EmailPermanentError),
        (401, EmailPermanentError),
        (403, EmailPermanentError),
        (429, EmailTemporaryError),
        (500, EmailTemporaryError),
        (503, EmailTemporaryError),
    ],
)
async def test__maileroo__errors(status_code, error):
    sender = _maileroo(lambda request: httpx.Response(status_code))

    with pytest.raises(error):
        await sender.send(MESSAGE)


async def test__maileroo__timeout_is_temporary():
    def handler(request):
        raise httpx.ConnectTimeout("timeout")

    with pytest.raises(EmailTemporaryError):
        await _maileroo(handler).send(MESSAGE)


async def test__console__logs_message():
    with structlog.testing.capture_logs() as logs:
        await ConsoleEmailSender().send(MESSAGE)

    assert logs[0]["event"] == "email_console"
    assert logs[0]["to"] == "to@example.com"
    assert logs[0]["subject"] == "Тема"
    assert logs[0]["text"] == "Привет"
