from typing import Any

from pydantic import TypeAdapter

from src.constants.permissions import Permission
from src.dto.common import SuccessOperationDTO
from src.dto.roles import RoleCreateDTO, RoleDTO, RoleUpdateDTO
from tests.endpoints.base import BaseEndpoints
from tests.endpoints.response import ResponseWrapper


class RolesEndpoints(BaseEndpoints):
    async def get_all(self, token: str | None = None) -> ResponseWrapper[list[RoleDTO]]:
        response = await self._client.get("/api/v1/roles", headers=self.bearer_headers(token))
        return ResponseWrapper(response, TypeAdapter(list[RoleDTO]))

    async def create(self, data: RoleCreateDTO | dict[str, Any], token: str | None = None) -> ResponseWrapper[RoleDTO]:
        response = await self._client.post("/api/v1/roles", json=self.to_json(data), headers=self.bearer_headers(token))
        return ResponseWrapper(response, RoleDTO)

    async def update(
        self, role_id: int, data: RoleUpdateDTO | dict[str, Any], token: str | None = None
    ) -> ResponseWrapper[RoleDTO]:
        response = await self._client.put(
            f"/api/v1/roles/{role_id}", json=self.to_json(data), headers=self.bearer_headers(token)
        )
        return ResponseWrapper(response, RoleDTO)

    async def delete(self, role_id: int, token: str | None = None) -> ResponseWrapper[SuccessOperationDTO]:
        response = await self._client.delete(f"/api/v1/roles/{role_id}", headers=self.bearer_headers(token))
        return ResponseWrapper(response, SuccessOperationDTO)


class PermissionsEndpoints(BaseEndpoints):
    async def get_all(self, token: str | None = None) -> ResponseWrapper[list[Permission]]:
        response = await self._client.get("/api/v1/permissions", headers=self.bearer_headers(token))
        return ResponseWrapper(response, TypeAdapter(list[Permission]))
