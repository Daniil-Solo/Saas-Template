import logging
import sys

import structlog
from structlog.typing import Processor

from src.settings import LoggingSettings

# Метка на обработчике, чтобы повторный setup_logging заменял только свой обработчик
_HANDLER_MARK = "_observability_handler"


def setup_logging(settings: LoggingSettings) -> None:
    """Настраивает structlog и направляет стандартный logging (uvicorn, SQLAlchemy и др.) в тот же формат."""
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.ExtraAdder(),
    ]
    renderer: Processor
    if settings.format == "json":
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
        )
    )
    setattr(handler, _HANDLER_MARK, True)

    root = logging.getLogger()
    for existing in list(root.handlers):
        if getattr(existing, _HANDLER_MARK, False):
            root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(settings.level)

    # uvicorn пишет через собственные обработчики; отдаём его записи корневому, access-лог заменяет middleware
    for name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
        uvicorn_logger.disabled = False  # fileConfig (alembic) мог отключить уже созданные логгеры
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = False
