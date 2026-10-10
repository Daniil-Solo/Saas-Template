from email.message import EmailMessage as MimeMessage
from email.utils import formataddr

import aiosmtplib

from src.dto.emails import EmailMessage
from src.infrastructure.email_sender.exceptions import EmailPermanentError, EmailTemporaryError
from src.infrastructure.email_sender.interface import EmailSender
from src.settings import EmailSettings, SmtpSettings


class SmtpEmailSender(EmailSender):
    def __init__(self, email_settings: EmailSettings, smtp_settings: SmtpSettings) -> None:
        self._email = email_settings
        self._smtp = smtp_settings

    def _build(self, message: EmailMessage) -> MimeMessage:
        mime = MimeMessage()
        mime["From"] = formataddr((self._email.from_display_name, self._email.from_address))
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime.set_content(message.text)
        mime.add_alternative(message.html, subtype="html")
        return mime

    async def send(self, message: EmailMessage) -> None:
        settings = self._smtp
        try:
            await aiosmtplib.send(
                self._build(message),
                hostname=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_tls=settings.tls == "ssl",
                start_tls=settings.tls == "starttls",
                timeout=settings.timeout,
            )
        except aiosmtplib.SMTPResponseException as exc:
            # 4xx - «попробуйте позже», 5xx - отказ (в т.ч. неверная авторизация или адрес)
            if 400 <= exc.code < 500:
                raise EmailTemporaryError(f"SMTP {exc.code}") from exc
            raise EmailPermanentError(f"SMTP {exc.code}") from exc
        except aiosmtplib.SMTPRecipientsRefused as exc:
            raise EmailPermanentError("SMTP: получатель отклонён") from exc
        except (aiosmtplib.SMTPException, OSError, TimeoutError) as exc:
            raise EmailTemporaryError(f"SMTP: {type(exc).__name__}") from exc
