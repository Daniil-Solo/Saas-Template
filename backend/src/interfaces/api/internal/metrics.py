from fastapi import APIRouter, Response

from src.infrastructure.observability.metrics import METRICS_CONTENT_TYPE, render_metrics

router = APIRouter(prefix="/internal/metrics", tags=["internal"])


@router.get("", include_in_schema=False)
async def metrics_endpoint() -> Response:
    return Response(content=render_metrics(), media_type=METRICS_CONTENT_TYPE)
