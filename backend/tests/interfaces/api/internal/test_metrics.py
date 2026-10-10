from httpx import ASGITransport, AsyncClient

from src.interfaces.api.app import create_app
from src.settings import MetricsSettings, get_settings
from tests.helpers.auth import make_token


async def test__success__format_and_standard_metrics(container, api):
    response = await api.internal.metrics()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in response.text
    assert "process_cpu_seconds_total" in response.text


async def test__success__route_template_is_used(container, api):
    await api.users.me(make_token(1))

    text = (await api.internal.metrics()).text

    assert 'http_requests_total{method="GET",route="/api/v1/users/me",status="401"}' in text
    assert 'http_request_duration_seconds_count{method="GET",route="/api/v1/users/me"}' in text


async def test__success__path_params_are_not_in_labels(container, api):
    await api.internal.get("/api/v1/organizations/123456789")

    text = (await api.internal.metrics()).text

    assert "123456789" not in text
    assert 'route="/api/v1/organizations/{org_id}"' in text


async def test__success__internal_requests_are_not_counted(container, api):
    (await api.internal.health()).validate()
    await api.internal.metrics()

    text = (await api.internal.metrics()).text

    assert "/api/internal" not in text


async def test__success__unknown_route_is_unmatched(container, api):
    response = await api.internal.get("/api/definitely/not/exists/987654")

    text = (await api.internal.metrics()).text

    assert response.status_code == 404
    assert 'route="unmatched",status="404"' in text
    assert "987654" not in text


async def test__success__in_progress_gauge_is_exported(container, api):
    text = (await api.internal.metrics()).text

    assert "# TYPE http_requests_in_progress gauge" in text


async def test__failed__metrics_disabled(container):
    settings = get_settings().model_copy(update={"metrics": MetricsSettings(enabled=False)})
    app = create_app(settings)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/internal/metrics")

    assert response.status_code == 404
