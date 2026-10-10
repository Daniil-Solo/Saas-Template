from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse
import structlog

from src.application.auth import bootstrap
from src.application.exceptions import ApplicationError
from src.di.container import init_container, shutdown_container
from src.dto.common import ErrorDTO
from src.infrastructure.observability.logging import setup_logging
from src.infrastructure.observability.sentry import setup_sentry
from src.interfaces.api.error_status_mapping import get_status_code
from src.interfaces.api.internal import internal_router
from src.interfaces.api.internal.metrics import router as metrics_router
from src.interfaces.api.middleware import REQUEST_ID_HEADER, REQUEST_ID_SCOPE_KEY, ObservabilityMiddleware
from src.interfaces.api.v1 import v1_router
from src.settings import Settings, get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    container = await init_container()
    await bootstrap.ensure_admin()
    try:
        yield
    finally:
        await shutdown_container(container)


async def application_error_handler(_: Request, error: ApplicationError) -> JSONResponse:
    status_code = get_status_code(error)
    headers = {"WWW-Authenticate": "Bearer"} if status_code == status.HTTP_401_UNAUTHORIZED else None
    body = ErrorDTO(code=error.code, message=error.message)
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


async def unhandled_error_handler(request: Request, _: Exception) -> JSONResponse:
    """Ответ на непредвиденный сбой: в теле единый формат ошибки, в заголовке - id запроса для обращения в поддержку."""
    body = ErrorDTO(code="internal_error", message="Внутренняя ошибка сервера")
    headers = {REQUEST_ID_HEADER: request.scope.get(REQUEST_ID_SCOPE_KEY, "")}
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body.model_dump(), headers=headers)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.logging)
    setup_sentry(settings.sentry, settings.app, ignored_exceptions=(ApplicationError,))
    if settings.email.backend == "console":
        logger.warning(
            "email_console_backend_enabled",
            detail="письма не отправляются, а пишутся в лог; задайте EMAIL_BACKEND=smtp|maileroo на продакшене",
        )

    app = FastAPI(title="Backend", lifespan=lifespan)
    app.add_exception_handler(ApplicationError, application_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.add_middleware(ObservabilityMiddleware, metrics_enabled=settings.metrics.enabled)

    api_router = APIRouter(prefix="/api")
    api_router.include_router(v1_router)
    api_router.include_router(internal_router)
    if settings.metrics.enabled:
        api_router.include_router(metrics_router)
    app.include_router(api_router)
    return app


app = create_app()
