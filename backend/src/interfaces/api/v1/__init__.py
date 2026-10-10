from fastapi import APIRouter

from src.interfaces.api.v1.auth.router import router as auth_router
from src.interfaces.api.v1.invitations.router import router as invitations_router
from src.interfaces.api.v1.notifications.router import router as notifications_router
from src.interfaces.api.v1.organizations.router import router as organizations_router
from src.interfaces.api.v1.permissions.router import router as permissions_router
from src.interfaces.api.v1.roles.router import router as roles_router
from src.interfaces.api.v1.users.router import router as users_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])
v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(organizations_router)
v1_router.include_router(roles_router)
v1_router.include_router(invitations_router)
v1_router.include_router(permissions_router)
v1_router.include_router(notifications_router)

__all__ = ["v1_router"]
