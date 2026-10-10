from typing import Any

from fastapi import APIRouter, Depends, status

from src.application.roles import roles as roles_service
from src.dto.common import ErrorDTO, SuccessOperationDTO
from src.dto.roles import RoleCreateDTO, RoleDTO, RoleUpdateDTO
from src.dto.users import UserDTO
from src.interfaces.api.dependencies import get_current_admin, get_current_user

router = APIRouter(prefix="/roles", tags=["roles"])

ADMIN_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {"model": ErrorDTO, "description": "Не администратор системы (admin_required)"}
}
NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorDTO, "description": "Роль не найдена (role_not_found)"}
}
NAME_EXISTS_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_409_CONFLICT: {"model": ErrorDTO, "description": "Имя роли занято (role_name_exists)"}
}


@router.get("", response_model=list[RoleDTO], summary="Список ролей")
async def list_roles_endpoint(user: UserDTO = Depends(get_current_user)) -> list[RoleDTO]:
    return await roles_service.get_all()


@router.post(
    "",
    response_model=RoleDTO,
    summary="Создать роль (администратор)",
    responses={**ADMIN_RESPONSE, **NAME_EXISTS_RESPONSE},
)
async def create_role_endpoint(data: RoleCreateDTO, admin: UserDTO = Depends(get_current_admin)) -> RoleDTO:
    return await roles_service.create(data)


@router.put(
    "/{role_id}",
    response_model=RoleDTO,
    summary="Изменить роль (администратор)",
    responses={**ADMIN_RESPONSE, **NOT_FOUND_RESPONSE, **NAME_EXISTS_RESPONSE},
)
async def update_role_endpoint(
    role_id: int,
    data: RoleUpdateDTO,
    admin: UserDTO = Depends(get_current_admin),
) -> RoleDTO:
    return await roles_service.update(role_id, data)


@router.delete(
    "/{role_id}",
    response_model=SuccessOperationDTO,
    summary="Удалить роль (администратор)",
    responses={**ADMIN_RESPONSE, **NOT_FOUND_RESPONSE},
)
async def delete_role_endpoint(role_id: int, admin: UserDTO = Depends(get_current_admin)) -> SuccessOperationDTO:
    return await roles_service.delete(role_id)
