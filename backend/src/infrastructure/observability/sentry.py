import sentry_sdk
from sentry_sdk.types import Event, Hint

from src.settings import AppSettings, SentrySettings


def setup_sentry(
    settings: SentrySettings,
    app_settings: AppSettings,
    ignored_exceptions: tuple[type[BaseException], ...] = (),
) -> bool:
    """Включает отправку непредвиденных ошибок в Sentry. Без DSN ничего не делает и наружу ничего не отправляет."""
    if settings.dsn is None:
        return False

    def before_send(event: Event, hint: Hint) -> Event | None:
        exc_info = hint.get("exc_info")
        if exc_info is not None and isinstance(exc_info[1], ignored_exceptions):
            return None
        return event

    sentry_sdk.init(
        dsn=settings.dsn,
        environment=settings.environment or app_settings.env,
        release=settings.release,
        traces_sample_rate=settings.traces_sample_rate,
        send_default_pii=False,
        max_request_body_size="never",
        include_local_variables=False,
        before_send=before_send,
    )
    return True
