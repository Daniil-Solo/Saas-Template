from dataclasses import dataclass

from src.constants.tasks import TaskName
from src.dto.common import BaseDTO
from src.dto.emails import EmailMessage
from src.infrastructure.email_sender.interface import EmailSender
from src.infrastructure.queue.interface import TaskQueue


@dataclass
class EnqueuedTask:
    task: TaskName
    payload: BaseDTO
    job_id: str | None


class FakeTaskQueue(TaskQueue):
    """Копит поставленные задачи; повторный `job_id` не дублируется, как в arq."""

    def __init__(self) -> None:
        self.tasks: list[EnqueuedTask] = []

    async def enqueue(self, task: TaskName, payload: BaseDTO, job_id: str | None = None) -> None:
        if job_id is not None and any(item.job_id == job_id for item in self.tasks):
            return
        self.tasks.append(EnqueuedTask(task=task, payload=payload, job_id=job_id))


class FakeEmailSender(EmailSender):
    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []
        self.error: Exception | None = None

    async def send(self, message: EmailMessage) -> None:
        if self.error is not None:
            raise self.error
        self.messages.append(message)
