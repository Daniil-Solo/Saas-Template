import pytest
import sentry_sdk

from src.application.exceptions import ApplicationError, InvalidCredentialsError
from src.infrastructure.observability import context
from src.infrastructure.observability.sentry import setup_sentry
from src.settings import AppSettings, SentrySettings

DSN = "http://public@localhost:1/1"


@pytest.fixture(autouse=True)
def reset_sentry():
    sentry_sdk.init(dsn=None)
    yield
    sentry_sdk.init(dsn=None)


def test__no_dsn__sentry_not_initialized():
    assert setup_sentry(SentrySettings(), AppSettings()) is False
    assert sentry_sdk.get_client().dsn is None


def test__dsn__initialized_with_settings():
    settings = SentrySettings(dsn=DSN, release="1.2.3", traces_sample_rate=0.5)

    assert setup_sentry(settings, AppSettings(env="prod")) is True

    options = sentry_sdk.get_client().options
    assert options["environment"] == "prod"
    assert options["release"] == "1.2.3"
    assert options["traces_sample_rate"] == 0.5
    assert options["send_default_pii"] is False
    assert options["max_request_body_size"] == "never"


def test__dsn__explicit_environment_wins():
    setup_sentry(SentrySettings(dsn=DSN, environment="staging"), AppSettings(env="prod"))

    assert sentry_sdk.get_client().options["environment"] == "staging"


def test__application_error_is_dropped():
    setup_sentry(SentrySettings(dsn=DSN), AppSettings(), ignored_exceptions=(ApplicationError,))
    before_send = sentry_sdk.get_client().options["before_send"]
    event = {"message": "x"}

    expected = InvalidCredentialsError()
    unexpected = RuntimeError("boom")

    assert before_send(event, {"exc_info": (type(expected), expected, None)}) is None
    assert before_send(event, {"exc_info": (type(unexpected), unexpected, None)}) == event
    assert before_send(event, {}) == event


def test__event_has_only_user_id_and_request_id():
    events: list[dict] = []
    sentry_sdk.init(dsn=DSN, transport=events.append, send_default_pii=False)
    context.bind_request_id("req-12345678")
    context.bind_user(7)

    sentry_sdk.capture_message("check")
    sentry_sdk.flush()

    assert events[0]["user"] == {"id": "7"}
    assert events[0]["tags"]["request_id"] == "req-12345678"
