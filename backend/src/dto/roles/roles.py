import datetime

from pydantic import Field

from src.constants.permissions import Permission
from src.dto.common import BaseDTO


class RoleCreateDTO(BaseDTO):
    name: str = Field(min_length=1, max_length=255, description="Название роли (уникально)")
    permissions: list[Permission] = Field(default_factory=list, description="Права, входящие в роль")


class RoleUpdateDTO(BaseDTO):
    name: str | None = Field(default=None, min_length=1, max_length=255, description="Новое название роли")
    permissions: list[Permission] | None = Field(default=None, description="Новый полный набор прав роли")


class RoleDTO(BaseDTO):
    id: int = Field(description="ID роли")
    name: str = Field(description="Название роли")
    permissions: list[Permission] = Field(description="Права, входящие в роль")
    created_at: datetime.datetime = Field(description="Дата создания")
