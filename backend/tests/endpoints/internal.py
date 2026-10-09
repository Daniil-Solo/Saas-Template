from src.dto.common import SuccessOperationDTO
from tests.endpoints.base import BaseEndpoints
from tests.endpoints.response import ResponseWrapper


class InternalEndpoints(BaseEndpoints):
    async def health(self) -> ResponseWrapper[SuccessOperationDTO]:
        response = await self._client.get("/api/internal/health")
        return ResponseWrapper(response, SuccessOperationDTO)
