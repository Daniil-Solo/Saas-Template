import datetime

from pydantic import Field

from src.constants.permissions import Permission
from src.dto.common import BaseDTO
from src.dto.roles import RoleDTO


class OrganizationCreateDTO(BaseDTO):
    name: str = Field(min_length=1, max_length=255, description="Название организации")


class OrganizationDTO(BaseDTO):
    id: int = Field(description="ID организации")
    name: str = Field(description="Название организации")
    created_by_id: int = Field(description="ID пользователя-создателя")
    created_at: datetime.datetime = Field(description="Дата создания")


class OrganizationDetailDTO(OrganizationDTO):
    permissions: list[Permission] = Field(description="Права текущего пользователя в организации")
    is_creator: bool = Field(description="Является ли текущий пользователь создателем организации")


class OrganizationAccessDTO(BaseDTO):
    """Доступ пользователя к организации: внутренний DTO, наружу не отдаётся."""

    organization_id: int = Field(description="ID организации")
    member_id: int = Field(description="ID участника")
    user_id: int = Field(description="ID пользователя")
    permissions: set[Permission] = Field(description="Эффективные права (для создателя - все)")
    is_creator: bool = Field(description="Является ли пользователь создателем организации")


class MemberUserDTO(BaseDTO):
    id: int = Field(description="ID пользователя")
    fullname: str = Field(description="ФИО пользователя")
    email: str = Field(description="Email пользователя")


class MemberDTO(BaseDTO):
    id: int = Field(description="ID участника")
    organization_id: int = Field(description="ID организации")
    user: MemberUserDTO = Field(description="Пользователь")
    roles: list[RoleDTO] = Field(description="Роли участника")
    is_creator: bool = Field(description="Является ли участник создателем организации")
    created_at: datetime.datetime = Field(description="Дата вступления")


class MemberRolesUpdateDTO(BaseDTO):
    role_ids: list[int] = Field(description="Полный набор ID ролей участника")
