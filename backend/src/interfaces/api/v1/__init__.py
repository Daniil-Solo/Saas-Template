from fastapi import APIRouter

from src.interfaces.api.v1.auth.router import router as auth_router
from src.interfaces.api.v1.users.router import router as users_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])
v1_router.include_router(auth_router)
v1_router.include_router(users_router)

__all__ = ["v1_router"]
