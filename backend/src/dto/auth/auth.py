from pydantic import Field

from src.dto.common import BaseDTO, NormalizedEmail


class UserRegisterDTO(BaseDTO):
    fullname: str = Field(min_length=1, max_length=255, description="ФИО пользователя")
    email: NormalizedEmail = Field(description="Email пользователя")
    password: str = Field(min_length=8, max_length=128, description="Пароль (от 8 до 128 символов)")


class UserLoginDTO(BaseDTO):
    email: NormalizedEmail = Field(description="Email пользователя")
    password: str = Field(min_length=1, max_length=128, description="Пароль")


class TokenDTO(BaseDTO):
    access_token: str = Field(description="JWT access-токен")
    token_type: str = Field(default="bearer", description="Тип токена")
