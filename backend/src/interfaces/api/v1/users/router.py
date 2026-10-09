from fastapi import APIRouter, Depends, status

from src.dto.common import ErrorDTO
from src.dto.users import UserDTO
from src.interfaces.api.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserDTO,
    summary="Информация о текущем пользователе",
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorDTO, "description": "Токен некорректен (invalid_token)"}},
)
async def get_me_endpoint(user: UserDTO = Depends(get_current_user)) -> UserDTO:
    return user
