import datetime

from pydantic import Field

from src.dto.common import BaseDTO, NormalizedEmail


class UserCreateDTO(BaseDTO):
    fullname: str = Field(min_length=1, max_length=255, description="ФИО пользователя")
    email: NormalizedEmail = Field(description="Email пользователя (в нижнем регистре)")
    hashed_password: str = Field(description="Хеш пароля")
    is_verified: bool = Field(default=False, description="Подтвержден ли email")
    is_admin: bool = Field(default=False, description="Является ли пользователь администратором")


class UserDTO(BaseDTO):
    id: int = Field(description="ID пользователя")
    fullname: str = Field(description="ФИО пользователя")
    email: str = Field(description="Email пользователя")
    is_verified: bool = Field(description="Подтвержден ли email")
    is_admin: bool = Field(description="Является ли пользователь администратором")
    created_at: datetime.datetime = Field(description="Дата создания")


class UserWithPasswordDTO(UserDTO):
    """Внутренний DTO с хешем пароля. Наружу (в API) не отдается."""

    hashed_password: str = Field(description="Хеш пароля")
