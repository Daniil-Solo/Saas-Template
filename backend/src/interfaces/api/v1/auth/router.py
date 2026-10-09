from fastapi import APIRouter, status

from src.application.auth import auth as auth_service
from src.dto.auth import TokenDTO, UserLoginDTO, UserRegisterDTO
from src.dto.common import ErrorDTO

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenDTO,
    summary="Регистрация пользователя",
    responses={status.HTTP_409_CONFLICT: {"model": ErrorDTO, "description": "Email уже занят (user_email_exists)"}},
)
async def register_endpoint(data: UserRegisterDTO) -> TokenDTO:
    return await auth_service.register(data)


@router.post(
    "/login",
    response_model=TokenDTO,
    summary="Вход по email и паролю",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorDTO,
            "description": "Неверный email или пароль (invalid_credentials)",
        }
    },
)
async def login_endpoint(data: UserLoginDTO) -> TokenDTO:
    return await auth_service.login(data)
