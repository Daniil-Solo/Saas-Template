import re

from httpx import ASGITransport, AsyncClient
import pytest
import structlog
from structlog.testing import capture_logs

from src.interfaces.api.app import create_app
from tests.factories.users import UserRegisterFactory
from tests.helpers.auth import make_token
from tests.helpers.users import create_users

HEX_ID = re.compile(r"^[0-9a-f]{32}$")


def _capture():
    return capture_logs(processors=[structlog.contextvars.merge_contextvars])


def _request_logs(logs: list[dict]) -> list[dict]:
    return [log for log in logs if log["event"] == "http_request"]


async def test__success__id_is_generated(container, api):
    response = (await api.internal.health()).response

    assert HEX_ID.match(response.headers["X-Request-ID"])


async def test__success__valid_incoming_id_is_kept(container, api):
    response = (await api.internal.health({"X-Request-ID": "client-req-12345"})).response

    assert response.headers["X-Request-ID"] == "client-req-12345"


@pytest.mark.parametrize("value", ["short", "x" * 65, "bad id with spaces!"])
async def test__success__invalid_incoming_id_is_replaced(container, api, value):
    response = await api.internal.get("/api/internal/health", {"X-Request-ID": value})

    assert response.headers["X-Request-ID"] != value
    assert HEX_ID.match(response.headers["X-Request-ID"])


async def test__success__id_in_error_response(container, api):
    response = await api.internal.get("/api/v1/users/me")

    assert response.status_code == 401
    assert HEX_ID.match(response.headers["X-Request-ID"])


async def test__success__request_log_has_id_and_route(uow, api):
    user = (await create_users(uow))[0]

    with _capture() as logs:
        response = await api.internal.get("/api/v1/users/me", {"Authorization": f"Bearer {make_token(user.id)}"})

    [log] = _request_logs(logs)
    assert log["request_id"] == response.headers["X-Request-ID"]
    assert log["method"] == "GET"
    assert log["path"] == "/api/v1/users/me"
    assert log["status"] == 200
    assert log["duration_ms"] >= 0
    assert log["user_id"] == user.id
    assert log["log_level"] == "info"


async def test__success__request_log_uses_route_template_not_actual_path(container, api):
    with _capture() as logs:
        await api.internal.get("/api/v1/organizations/424242?token=secret")

    [log] = _request_logs(logs)
    assert log["path"] == "/api/v1/organizations/{org_id}"
    assert "secret" not in str(log)


async def test__success__internal_requests_are_not_logged(container, api):
    with _capture() as logs:
        (await api.internal.health()).validate()
        await api.internal.metrics()

    assert _request_logs(logs) == []


async def test__success__user_id_does_not_leak_between_requests(uow, api):
    user = (await create_users(uow))[0]
    await api.internal.get("/api/v1/users/me", {"Authorization": f"Bearer {make_token(user.id)}"})

    with _capture() as logs:
        await api.internal.get("/api/v1/users/me")

    [log] = _request_logs(logs)
    assert "user_id" not in log


async def test__success__unhandled_error_returns_500_with_id(container):
    app = create_app()

    async def boom() -> None:
        raise RuntimeError("boom")

    app.add_api_route("/api/boom", boom)
    transport = ASGITransport(app=app, raise_app_exceptions=False)

    with _capture() as logs:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/boom")

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert HEX_ID.match(response.headers["X-Request-ID"])
    [log] = _request_logs(logs)
    assert log["log_level"] == "error"
    assert log["status"] == 500
    assert isinstance(log["exc_info"], RuntimeError)


async def test__success__no_pii_in_auth_logs(container, api):
    data = UserRegisterFactory.build()

    with _capture() as logs:
        (await api.auth.register(data)).validate()
        await api.auth.login({"email": data.email, "password": data.password})
        await api.auth.login({"email": data.email, "password": "wrong-password-1"})

    rendered = str(logs)
    assert len(_request_logs(logs)) == 3
    assert data.email not in rendered
    assert data.password not in rendered
    assert data.fullname not in rendered
    assert "wrong-password-1" not in rendered
