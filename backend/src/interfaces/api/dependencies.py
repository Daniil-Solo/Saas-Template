from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.auth import auth as auth_service
from src.application.exceptions import InvalidTokenError
from src.dto.users import UserDTO

# auto_error=False: отсутствие токена обрабатываем сами, чтобы вернуть единый формат ошибки
bearer_scheme = HTTPBearer(auto_error=False, description="JWT access-токен из /api/v1/auth/login или /register")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserDTO:
    if credentials is None:
        raise InvalidTokenError
    return await auth_service.authenticate(credentials.credentials)
