from pydantic import ValidationError
import pytest

from src.settings import SentrySettings, Settings

REQUIRED_ENV = {
    "DB_HOST": "db",
    "DB_USER": "user",
    "DB_PASSWORD": "pass",
    "DB_NAME": "name",
    "AUTH_SECRET_KEY": "secret",
}


@pytest.fixture
def env(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    return monkeypatch


def test__success__groups_are_collected(env):
    env.setenv("LOG_LEVEL", "WARNING")
    env.setenv("LOG_FORMAT", "console")
    env.setenv("METRICS_ENABLED", "false")
    env.setenv("ENV", "prod")

    settings = Settings()

    assert settings.db.host == "db"
    assert settings.auth.secret_key == "secret"
    assert settings.logging.level == "WARNING"
    assert settings.logging.format == "console"
    assert settings.metrics.enabled is False
    assert settings.app.env == "prod"
    assert settings.invitations.ttl_days == 7


def test__success__defaults(env):
    for key in ("LOG_LEVEL", "LOG_FORMAT", "METRICS_ENABLED", "SENTRY_DSN", "SENTRY_TRACES_SAMPLE_RATE"):
        env.delenv(key, raising=False)

    settings = Settings()

    assert settings.logging.level == "INFO"
    assert settings.logging.format == "json"
    assert settings.metrics.enabled is True
    assert settings.sentry.dsn is None
    assert settings.sentry.traces_sample_rate == 0


def test__success__empty_sentry_dsn_is_none(env):
    env.setenv("SENTRY_DSN", "")
    env.setenv("SENTRY_ENVIRONMENT", "  ")

    settings = Settings()

    assert settings.sentry.dsn is None
    assert settings.sentry.environment is None


def test__failed__missing_required_value(env):
    env.delenv("AUTH_SECRET_KEY")

    with pytest.raises(ValidationError, match="secret_key"):
        Settings()


def test__failed__invalid_log_level(env):
    env.setenv("LOG_LEVEL", "TRACE")

    with pytest.raises(ValidationError, match="level"):
        Settings()


@pytest.mark.parametrize("rate", [-0.1, 1.1])
def test__failed__sentry_sample_rate_out_of_range(rate):
    with pytest.raises(ValidationError, match="traces_sample_rate"):
        SentrySettings(traces_sample_rate=rate)


def test__email__defaults_to_console(env):
    for key in ("EMAIL_BACKEND", "EMAIL_SMTP_HOST", "EMAIL_MAILEROO_API_KEY"):
        env.delenv(key, raising=False)

    settings = Settings()

    assert settings.email.backend == "console"


def test__email__smtp_requires_host(env):
    env.setenv("EMAIL_BACKEND", "smtp")
    env.setenv("EMAIL_SMTP_HOST", "")

    with pytest.raises(ValidationError, match="EMAIL_SMTP_HOST"):
        Settings()


def test__email__smtp_login_and_password_only_together(env):
    env.setenv("EMAIL_BACKEND", "smtp")
    env.setenv("EMAIL_SMTP_HOST", "mailpit")
    env.setenv("EMAIL_SMTP_USERNAME", "user")
    env.delenv("EMAIL_SMTP_PASSWORD", raising=False)

    with pytest.raises(ValidationError, match="EMAIL_SMTP_PASSWORD"):
        Settings()


def test__email__smtp_ok(env):
    env.setenv("EMAIL_BACKEND", "smtp")
    env.setenv("EMAIL_SMTP_HOST", "mailpit")
    env.setenv("EMAIL_SMTP_USERNAME", "")
    env.setenv("EMAIL_SMTP_PASSWORD", "")

    settings = Settings()

    assert settings.smtp.host == "mailpit"
    assert settings.smtp.username is None


def test__email__maileroo_requires_api_key(env):
    env.setenv("EMAIL_BACKEND", "maileroo")
    env.setenv("EMAIL_MAILEROO_API_KEY", "")

    with pytest.raises(ValidationError, match="EMAIL_MAILEROO_API_KEY"):
        Settings()


def test__email__console_needs_nothing_else(env):
    env.setenv("EMAIL_BACKEND", "console")
    env.setenv("EMAIL_SMTP_HOST", "")
    env.setenv("EMAIL_MAILEROO_API_KEY", "")

    Settings()


def test__redis_dsn(env):
    env.setenv("REDIS_HOST", "r")
    env.setenv("REDIS_PASSWORD", "p@ss")

    assert Settings().redis.dsn == "redis://:p%40ss@r:6379/0"
