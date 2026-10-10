from httpx import Response

from src.dto.common import SuccessOperationDTO
from tests.endpoints.base import BaseEndpoints
from tests.endpoints.response import ResponseWrapper


class InternalEndpoints(BaseEndpoints):
    async def health(self, headers: dict[str, str] | None = None) -> ResponseWrapper[SuccessOperationDTO]:
        response = await self._client.get("/api/internal/health", headers=headers)
        return ResponseWrapper(response, SuccessOperationDTO)

    async def metrics(self) -> Response:
        """Метрики Prometheus (текстовый формат, вне OpenAPI), поэтому сырой ответ без DTO."""
        return await self._client.get("/api/internal/metrics")

    async def get(self, path: str, headers: dict[str, str] | None = None) -> Response:
        """Произвольный GET (несуществующие маршруты и т.п.)."""
        return await self._client.get(path, headers=headers)
