from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Число обработанных HTTP-запросов",
    ["method", "route", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Длительность обработки HTTP-запроса, секунды",
    ["method", "route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Число HTTP-запросов в обработке",
    ["method"],
)

METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST


def render_metrics() -> bytes:
    return generate_latest()
