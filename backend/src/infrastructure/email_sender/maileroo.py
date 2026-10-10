import httpx

from src.dto.emails import EmailMessage
from src.infrastructure.email_sender.exceptions import EmailPermanentError, EmailTemporaryError
from src.infrastructure.email_sender.interface import EmailSender
from src.settings import EmailSettings, MailerooSettings

MAILEROO_URL = "https://smtp.maileroo.com/api/v2/emails"


class MailerooEmailSender(EmailSender):
    def __init__(
        self,
        email_settings: EmailSettings,
        maileroo_settings: MailerooSettings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._email = email_settings
        self._api_key = maileroo_settings.api_key or ""
        self._client = client or httpx.AsyncClient(timeout=10)

    async def send(self, message: EmailMessage) -> None:
        body = {
            "from": {"address": self._email.from_address, "display_name": self._email.from_display_name},
            "to": [{"address": message.to}],
            "subject": message.subject,
            "html": message.html,
            "plain": message.text,
        }
        try:
            response = await self._client.post(MAILEROO_URL, json=body, headers={"X-API-Key": self._api_key})
        except httpx.HTTPError as exc:
            raise EmailTemporaryError(f"Maileroo: {type(exc).__name__}") from exc
        if response.is_success:
            return
        if response.status_code == 429 or response.status_code >= 500:
            raise EmailTemporaryError(f"Maileroo: HTTP {response.status_code}")
        raise EmailPermanentError(f"Maileroo: HTTP {response.status_code}")
