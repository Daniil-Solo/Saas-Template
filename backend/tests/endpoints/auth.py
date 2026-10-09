from typing import Any

from src.dto.auth import TokenDTO, UserLoginDTO, UserRegisterDTO
from tests.endpoints.base import BaseEndpoints
from tests.endpoints.response import ResponseWrapper


class AuthEndpoints(BaseEndpoints):
    async def register(self, data: UserRegisterDTO | dict[str, Any]) -> ResponseWrapper[TokenDTO]:
        response = await self._client.post("/api/v1/auth/register", json=self.to_json(data))
        return ResponseWrapper(response, TokenDTO)

    async def login(self, data: UserLoginDTO | dict[str, Any]) -> ResponseWrapper[TokenDTO]:
        response = await self._client.post("/api/v1/auth/login", json=self.to_json(data))
        return ResponseWrapper(response, TokenDTO)
