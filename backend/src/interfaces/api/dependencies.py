from collections.abc import Awaitable, Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.auth import auth as auth_service
from src.application.exceptions import AdminRequiredError, InvalidTokenError, PermissionDeniedError
from src.application.organizations import organizations as organizations_service
from src.constants.permissions import Permission
from src.dto.organizations import OrganizationAccessDTO
from src.dto.users import UserDTO
from src.infrastructure.observability import context as observability_context

# auto_error=False: отсутствие токена обрабатываем сами, чтобы вернуть единый формат ошибки
bearer_scheme = HTTPBearer(auto_error=False, description="JWT access-токен из /api/v1/auth/login или /register")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserDTO:
    if credentials is None:
        raise InvalidTokenError
    user = await auth_service.authenticate(credentials.credentials)
    observability_context.bind_user(user.id)
    return user


async def get_current_admin(user: UserDTO = Depends(get_current_user)) -> UserDTO:
    if not user.is_admin:
        raise AdminRequiredError
    return user


async def get_organization_access(
    org_id: int,
    user: UserDTO = Depends(get_current_user),
) -> OrganizationAccessDTO:
    """Доступ участника к организации из пути; не участник -> 404 organization_not_found."""
    return await organizations_service.get_access(org_id, user)


def require_permission(permission: Permission) -> Callable[..., Awaitable[OrganizationAccessDTO]]:
    async def dependency(
        access: OrganizationAccessDTO = Depends(get_organization_access),
    ) -> OrganizationAccessDTO:
        if permission not in access.permissions:
            raise PermissionDeniedError
        return access

    return dependency


require_members_manage = require_permission(Permission.MEMBERS_MANAGE)
require_invitations_manage = require_permission(Permission.INVITATIONS_MANAGE)
