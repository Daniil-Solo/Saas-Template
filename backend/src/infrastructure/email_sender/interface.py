from abc import ABC, abstractmethod

from src.dto.emails import EmailMessage


class EmailSender(ABC):
    @abstractmethod
    async def send(self, message: EmailMessage) -> None:
        """Отправляет письмо. Бросает `EmailTemporaryError` или `EmailPermanentError`."""
        raise NotImplementedError
