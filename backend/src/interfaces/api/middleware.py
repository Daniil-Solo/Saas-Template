import re
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
import structlog

from src.infrastructure.observability import context
from src.infrastructure.observability.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
)

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_SCOPE_KEY = "request_id"
INTERNAL_PATH_PREFIX = "/api/internal/"
UNMATCHED_ROUTE = "unmatched"

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")
_KNOWN_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})

logger = structlog.get_logger("http")


def _resolve_request_id(scope: Scope) -> str:
    for name, value in scope["headers"]:
        if name == b"x-request-id":
            candidate: str = value.decode("latin-1")
            if _REQUEST_ID_RE.fullmatch(candidate):
                return candidate
            break
    return uuid.uuid4().hex


def _route_template(scope: Scope) -> str | None:
    """Шаблон пути вида `/api/v1/organizations/{org_id}`; None, если маршрут не найден.

    FastAPI хранит префиксы вложенных роутеров в `scope["fastapi"]["included_router"]`, а у самого маршрута путь
    относительный, поэтому полный шаблон собирается из префикса и пути маршрута.
    """
    route = scope.get("route")
    if route is None:
        return None
    path: str | None = getattr(route, "path_format", None) or getattr(route, "path", None)
    if path is None:
        return None
    included_router = (scope.get("fastapi") or {}).get("included_router")
    prefix: str = getattr(getattr(included_router, "include_context", None), "prefix", "") or ""
    return prefix + path


class ObservabilityMiddleware:
    """Чистый ASGI-middleware: X-Request-ID, одна запись `http_request` на запрос и HTTP-метрики."""

    def __init__(self, app: ASGIApp, *, metrics_enabled: bool = True) -> None:
        self.app = app
        self.metrics_enabled = metrics_enabled

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _resolve_request_id(scope)
        scope[REQUEST_ID_SCOPE_KEY] = request_id
        context.clear_context()
        context.bind_request_id(request_id)

        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        # Служебные запросы (health, metrics) не логируем и не учитываем в метриках
        if scope["path"].startswith(INTERNAL_PATH_PREFIX):
            await self.app(scope, receive, send_wrapper)
            return

        method = scope["method"] if scope["method"] in _KNOWN_METHODS else "OTHER"
        in_progress = HTTP_REQUESTS_IN_PROGRESS.labels(method) if self.metrics_enabled else None
        if in_progress is not None:
            in_progress.inc()
        started = time.perf_counter()
        error: Exception | None = None
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            error = exc
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - started
            if in_progress is not None:
                in_progress.dec()
            template = _route_template(scope)
            if self.metrics_enabled:
                route = template or UNMATCHED_ROUTE
                HTTP_REQUESTS_TOTAL.labels(method, route, str(status_code)).inc()
                HTTP_REQUEST_DURATION_SECONDS.labels(method, route).observe(duration)
            log = logger.error if status_code >= 500 else logger.info
            log(
                "http_request",
                method=scope["method"],
                path=template or scope["path"],
                status=status_code,
                duration_ms=round(duration * 1000, 2),
                exc_info=error,
            )
            context.clear_context()
