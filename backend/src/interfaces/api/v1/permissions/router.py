from fastapi import APIRouter, Depends

from src.application.permissions import permissions as permissions_service
from src.constants.permissions import Permission
from src.dto.users import UserDTO
from src.interfaces.api.dependencies import get_current_user

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("", response_model=list[Permission], summary="Все права системы")
async def list_permissions_endpoint(user: UserDTO = Depends(get_current_user)) -> list[Permission]:
    return await permissions_service.get_all()
