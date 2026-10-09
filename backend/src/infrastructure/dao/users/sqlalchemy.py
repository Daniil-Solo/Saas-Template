import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import UserEmailExistsError, UserNotFoundError
from src.dto.users import UserCreateDTO, UserDTO, UserWithPasswordDTO
from src.infrastructure.dao.users.interface import UsersDAO
from src.infrastructure.sqlalchemy.models import users_table

EMAIL_UNIQUE_CONSTRAINT = "uq_users_email"


class SQLAlchemyUsersDAO(UsersDAO):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: UserCreateDTO) -> UserDTO:
        query = sa.insert(users_table).values(**data.model_dump()).returning(users_table)
        try:
            result = await self.session.execute(query)
        except IntegrityError as exc:
            # Защита от гонки: параллельные регистрации с одним email отсекает уникальный индекс
            if EMAIL_UNIQUE_CONSTRAINT in str(exc.orig):
                raise UserEmailExistsError from exc
            raise
        return UserDTO.model_validate(result.one())

    async def get_by_id(self, user_id: int) -> UserDTO:
        query = sa.select(users_table).where(users_table.c.id == user_id)
        result = await self.session.execute(query)
        row = result.one_or_none()
        if row is None:
            raise UserNotFoundError
        return UserDTO.model_validate(row)

    async def get_by_email(self, email: str) -> UserWithPasswordDTO:
        query = sa.select(users_table).where(users_table.c.email == email)
        result = await self.session.execute(query)
        row = result.one_or_none()
        if row is None:
            raise UserNotFoundError
        return UserWithPasswordDTO.model_validate(row)

    async def update_hashed_password(self, user_id: int, hashed_password: str) -> None:
        query = (
            sa.update(users_table)
            .where(users_table.c.id == user_id)
            .values(hashed_password=hashed_password)
            .returning(users_table.c.id)
        )
        result = await self.session.execute(query)
        if result.one_or_none() is None:
            raise UserNotFoundError
