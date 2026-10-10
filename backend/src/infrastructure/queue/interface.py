from abc import ABC, abstractmethod

from src.constants.tasks import TaskName
from src.dto.common import BaseDTO


class TaskQueue(ABC):
    @abstractmethod
    async def enqueue(self, task: TaskName, payload: BaseDTO, job_id: str | None = None) -> None:
        """Ставит задачу в очередь. Задача с тем же `job_id`, пока первая в очереди или выполняется, не дублируется."""
        raise NotImplementedError
