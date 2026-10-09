from src.dto.auth import UserRegisterDTO
from src.dto.users import UserCreateDTO, UserDTO
from src.infrastructure.auth.password import hash_password
from src.infrastructure.sqlalchemy.uow import UnitOfWork
from tests.factories.users import UserRegisterFactory


async def create_users(
    uow: UnitOfWork,
    size: int = 1,
    is_admin: bool = False,
    hashed_password: str | None = None,
) -> list[UserDTO]:
    """Создает пользователей напрямую в БД с паролем TEST_PASSWORD (или с переданным готовым хешем)."""
    data_list: list[UserRegisterDTO] = UserRegisterFactory.build_batch(size=size)
    users = []
    async with uow.connection():
        for data in data_list:
            user = await uow.users.create(
                UserCreateDTO(
                    fullname=data.fullname,
                    email=data.email,
                    hashed_password=hashed_password or await hash_password(data.password),
                    is_verified=True,
                    is_admin=is_admin,
                )
            )
            users.append(user)
    return users
