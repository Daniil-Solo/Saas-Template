from fastapi import APIRouter

from src.dto.common import SuccessOperationDTO

router = APIRouter(prefix="/health", tags=["internal"])


@router.get("", response_model=SuccessOperationDTO, summary="Проверка работоспособности")
async def health_endpoint() -> SuccessOperationDTO:
    return SuccessOperationDTO(message="ok")
