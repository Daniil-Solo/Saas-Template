import io
import json
import logging

import pytest
import structlog

from src.infrastructure.observability.logging import _HANDLER_MARK, setup_logging
from src.settings import LoggingSettings, get_settings


def _install(settings: LoggingSettings) -> io.StringIO:
    """Настраивает логирование и перенаправляет наш обработчик в буфер."""
    setup_logging(settings)
    stream = io.StringIO()
    handler = next(h for h in logging.getLogger().handlers if getattr(h, _HANDLER_MARK, False))
    assert isinstance(handler, logging.StreamHandler)
    handler.setStream(stream)
    return stream


@pytest.fixture(autouse=True)
def restore_logging():
    yield
    structlog.contextvars.clear_contextvars()
    setup_logging(get_settings().logging)


def test__json__structlog_record():
    stream = _install(LoggingSettings(level="INFO", format="json"))
    structlog.contextvars.bind_contextvars(request_id="abc12345")

    structlog.get_logger("test").info("something_happened", answer=42)

    record = json.loads(stream.getvalue().strip())
    assert record["event"] == "something_happened"
    assert record["answer"] == 42
    assert record["level"] == "info"
    assert record["request_id"] == "abc12345"
    assert record["timestamp"].endswith("Z")


def test__json__exception_has_traceback():
    stream = _install(LoggingSettings(level="INFO", format="json"))

    try:
        raise ValueError("boom")
    except ValueError:
        structlog.get_logger("test").error("failed", exc_info=True)

    record = json.loads(stream.getvalue().strip())
    assert "ValueError: boom" in record["exception"]


def test__json__standard_logging_goes_through_structlog():
    stream = _install(LoggingSettings(level="INFO", format="json"))

    logging.getLogger("uvicorn.error").info("started")

    record = json.loads(stream.getvalue().strip())
    assert record["event"] == "started"
    assert record["level"] == "info"


def test__json__level_filters_records():
    stream = _install(LoggingSettings(level="WARNING", format="json"))

    structlog.get_logger("test").info("quiet")
    structlog.get_logger("test").warning("loud")

    lines = stream.getvalue().strip().splitlines()
    assert [json.loads(line)["event"] for line in lines] == ["loud"]


def test__console__human_readable():
    stream = _install(LoggingSettings(level="INFO", format="console"))

    structlog.get_logger("test").info("something_happened", answer=42)

    output = stream.getvalue()
    assert "something_happened" in output
    assert "answer" in output
    with pytest.raises(json.JSONDecodeError):
        json.loads(output)


def test__access_log_is_silenced():
    stream = _install(LoggingSettings(level="DEBUG", format="json"))

    logging.getLogger("uvicorn.access").info("GET / 200")

    assert stream.getvalue() == ""
