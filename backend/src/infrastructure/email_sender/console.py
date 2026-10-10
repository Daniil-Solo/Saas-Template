import structlog

from src.dto.emails import EmailMessage
from src.infrastructure.email_sender.interface import EmailSender

logger = structlog.get_logger(__name__)


class ConsoleEmailSender(EmailSender):
    """Только для разработки: пишет письмо в лог (с адресом и текстом) вместо отправки."""

    async def send(self, message: EmailMessage) -> None:
        logger.info("email_console", to=message.to, subject=message.subject, text=message.text)
