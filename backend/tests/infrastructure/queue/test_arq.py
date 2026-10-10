import uuid

from arq import create_pool
from arq.connections import RedisSettings as ArqRedisSettings

from src.constants.tasks import TaskName
from src.dto.tasks import SendInvitationEmailDTO
from src.infrastructure.queue.arq import init_task_queue
from src.settings import get_settings


async def test__enqueue_puts_job_and_deduplicates():
    redis = get_settings().redis
    job_id = f"test-{uuid.uuid4().hex}"
    generator = init_task_queue(redis)
    queue = await anext(generator)
    pool = await create_pool(
        ArqRedisSettings(host=redis.host, port=redis.port, database=redis.db, password=redis.password)
    )
    try:
        payload = SendInvitationEmailDTO(invitation_id=1, token="t")
        await queue.enqueue(TaskName.SEND_INVITATION_EMAIL, payload, job_id=job_id)
        await queue.enqueue(TaskName.SEND_INVITATION_EMAIL, payload, job_id=job_id)

        jobs = [job for job in await pool.queued_jobs() if job.job_id == job_id]
        assert len(jobs) == 1
        assert jobs[0].function == TaskName.SEND_INVITATION_EMAIL.value
        assert jobs[0].args == ({"invitation_id": 1, "token": "t"},)
    finally:
        await pool.delete(f"arq:job:{job_id}")
        await pool.zrem("arq:queue", job_id)
        await pool.aclose()
        await generator.aclose()
