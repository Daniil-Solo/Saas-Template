from collections.abc import AsyncGenerator

from arq import create_pool
from arq.connections import ArqRedis
from arq.connections import RedisSettings as ArqRedisSettings

from src.constants.tasks import TaskName
from src.dto.common import BaseDTO
from src.infrastructure.queue.interface import TaskQueue
from src.settings import RedisSettings


class ArqTaskQueue(TaskQueue):
    def __init__(self, pool: ArqRedis) -> None:
        self._pool = pool

    async def enqueue(self, task: TaskName, payload: BaseDTO, job_id: str | None = None) -> None:
        await self._pool.enqueue_job(task.value, payload.model_dump(mode="json"), _job_id=job_id)


async def init_task_queue(settings: RedisSettings) -> AsyncGenerator[ArqTaskQueue, None]:
    """Ресурс DI: пул соединений arq закрывается при остановке контейнера."""
    pool = await create_pool(
        ArqRedisSettings(
            host=settings.host,
            port=settings.port,
            database=settings.db,
            password=settings.password,
        )
    )
    try:
        yield ArqTaskQueue(pool)
    finally:
        await pool.aclose()
