import sentry_sdk
import structlog


def bind_request_id(request_id: str) -> None:
    structlog.contextvars.bind_contextvars(request_id=request_id)
    sentry_sdk.set_tag("request_id", request_id)


def bind_user(user_id: int) -> None:
    """Только идентификатор пользователя: email, ФИО и токены в логи и Sentry не попадают."""
    structlog.contextvars.bind_contextvars(user_id=user_id)
    sentry_sdk.set_user({"id": str(user_id)})


def clear_context() -> None:
    structlog.contextvars.clear_contextvars()
