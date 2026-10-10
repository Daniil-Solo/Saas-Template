import logging
from typing import Any

from arq.connections import RedisSettings as ArqRedisSettings
import structlog

from src.di.container import Container, init_container, shutdown_container
from src.infrastructure.observability.logging import setup_logging
from src.infrastructure.observability.sentry import setup_sentry
from src.interfaces.tasks.emails import MAX_TRIES, send_email, send_invitation_email
from src.settings import get_settings

logger = structlog.get_logger(__name__)

_settings = get_settings()


async def on_startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    setup_logging(settings.logging)
    setup_sentry(settings.sentry, settings.app)
    # arq пишет аргументы задач (адрес, токен приглашения) в INFO: скрываем, свои логи пишут сервисы
    logging.getLogger("arq.worker").setLevel(logging.WARNING)
    ctx["container"] = await init_container()
    if settings.email.backend == "console":
        logger.warning(
            "email_console_backend_enabled",
            detail="письма не отправляются, а пишутся в лог; задайте EMAIL_BACKEND=smtp|maileroo на продакшене",
        )


async def on_shutdown(ctx: dict[str, Any]) -> None:
    container: Container = ctx["container"]
    await shutdown_container(container)


class WorkerSettings:
    functions = [send_email, send_invitation_email]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = ArqRedisSettings(
        host=_settings.redis.host,
        port=_settings.redis.port,
        database=_settings.redis.db,
        password=_settings.redis.password,
    )
    max_tries = MAX_TRIES
    keep_result = 0
