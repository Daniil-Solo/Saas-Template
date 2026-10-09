import datetime

from dependency_injector.wiring import Provide, inject

from src.application.exceptions import InvalidCredentialsError, InvalidTokenError, UserNotFoundError
from src.di.container import Container
from src.dto.auth import TokenDTO, UserLoginDTO, UserRegisterDTO
from src.dto.users import UserCreateDTO, UserDTO
from src.infrastructure.auth import jwt as jwt_utils
from src.infrastructure.auth import password as password_utils
from src.infrastructure.sqlalchemy.uow import UnitOfWork
from src.settings import AuthSettings


def _create_token(user_id: int, auth_settings: AuthSettings) -> TokenDTO:
    access_token = jwt_utils.create_access_token(
        user_id=user_id,
        secret_key=auth_settings.secret_key,
        algorithm=auth_settings.algorithm,
        ttl=datetime.timedelta(minutes=auth_settings.access_token_ttl_minutes),
    )
    return TokenDTO(access_token=access_token)


@inject
async def register(
    data: UserRegisterDTO,
    uow: UnitOfWork = Provide[Container.uow],
    auth_settings: AuthSettings = Provide[Container.auth_settings],
) -> TokenDTO:
    user_data = UserCreateDTO(
        fullname=data.fullname,
        email=data.email,
        hashed_password=await password_utils.hash_password(data.password),
        # Упрощение шаблона: email считается подтвержденным сразу.
        # В реальном проекте здесь должна быть верификация email (письмо со ссылкой), а значение - False.
        is_verified=True,
    )
    async with uow.connection():
        user = await uow.users.create(user_data)
    return _create_token(user.id, auth_settings)


@inject
async def login(
    data: UserLoginDTO,
    uow: UnitOfWork = Provide[Container.uow],
    auth_settings: AuthSettings = Provide[Container.auth_settings],
) -> TokenDTO:
    async with uow.connection():
        try:
            user = await uow.users.get_by_email(data.email)
        except UserNotFoundError as exc:
            # Тратим то же время, что и на реального пользователя, и отдаем ту же ошибку:
            # по ответу нельзя определить, зарегистрирован ли email
            await password_utils.verify_dummy_password(data.password)
            raise InvalidCredentialsError from exc

        if not await password_utils.verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError

        if password_utils.needs_rehash(user.hashed_password):
            new_hash = await password_utils.hash_password(data.password)
            await uow.users.update_hashed_password(user.id, new_hash)

    return _create_token(user.id, auth_settings)


@inject
async def authenticate(
    token: str,
    uow: UnitOfWork = Provide[Container.uow],
    auth_settings: AuthSettings = Provide[Container.auth_settings],
) -> UserDTO:
    """Возвращает пользователя по access-токену или бросает InvalidTokenError."""
    try:
        user_id = jwt_utils.decode_access_token(token, auth_settings.secret_key, auth_settings.algorithm)
    except jwt_utils.TokenDecodeError as exc:
        raise InvalidTokenError from exc

    async with uow.connection():
        try:
            return await uow.users.get_by_id(user_id)
        except UserNotFoundError as exc:
            # Пользователь удален, а токен еще жив
            raise InvalidTokenError from exc
