import logging

from dependency_injector.wiring import Provide, inject

from src.application.exceptions import UserEmailExistsError, UserNotFoundError
from src.di.container import Container
from src.dto.users import UserCreateDTO
from src.infrastructure.auth import password as password_utils
from src.infrastructure.sqlalchemy.uow import UnitOfWork
from src.settings import AdminSettings

logger = logging.getLogger(__name__)


@inject
async def ensure_admin(
    uow: UnitOfWork = Provide[Container.uow],
    settings: AdminSettings = Provide[Container.admin_settings],
) -> None:
    """Создаёт администратора из ADMIN_EMAIL/ADMIN_PASSWORD, если такого пользователя ещё нет.

    Существующий пользователь не меняется (пароль и права остаются прежними).
    """
    if settings.email is None or settings.password is None:
        return
    email = settings.email.strip().lower()
    async with uow.connection():
        try:
            await uow.users.get_by_email(email)
        except UserNotFoundError:
            pass
        else:
            logger.info("Администратор %s уже существует", email)
            return
        data = UserCreateDTO(
            fullname="Administrator",
            email=email,
            hashed_password=await password_utils.hash_password(settings.password),
            is_verified=True,
            is_admin=True,
        )
        try:
            await uow.users.create(data)
        except UserEmailExistsError:
            # Параллельный старт другого экземпляра успел раньше
            return
    logger.info("Создан администратор %s", email)
