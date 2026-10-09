from fastapi import APIRouter

from src.interfaces.api.internal.health import router as health_router

internal_router = APIRouter(prefix="/internal", tags=["internal"])
internal_router.include_router(health_router)

__all__ = ["internal_router"]
