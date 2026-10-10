from typing import Any

from pydantic import TypeAdapter

from src.dto.common import SuccessOperationDTO
from src.dto.organizations import (
    MemberDTO,
    MemberRolesUpdateDTO,
    OrganizationCreateDTO,
    OrganizationDetailDTO,
    OrganizationDTO,
)
from tests.endpoints.base import BaseEndpoints
from tests.endpoints.response import ResponseWrapper


class OrganizationsEndpoints(BaseEndpoints):
    async def create(
        self, data: OrganizationCreateDTO | dict[str, Any], token: str | None = None
    ) -> ResponseWrapper[OrganizationDTO]:
        response = await self._client.post(
            "/api/v1/organizations", json=self.to_json(data), headers=self.bearer_headers(token)
        )
        return ResponseWrapper(response, OrganizationDTO)

    async def get_all(self, token: str | None = None) -> ResponseWrapper[list[OrganizationDTO]]:
        response = await self._client.get("/api/v1/organizations", headers=self.bearer_headers(token))
        return ResponseWrapper(response, TypeAdapter(list[OrganizationDTO]))

    async def get(self, org_id: int, token: str | None = None) -> ResponseWrapper[OrganizationDetailDTO]:
        response = await self._client.get(f"/api/v1/organizations/{org_id}", headers=self.bearer_headers(token))
        return ResponseWrapper(response, OrganizationDetailDTO)

    async def list_members(self, org_id: int, token: str | None = None) -> ResponseWrapper[list[MemberDTO]]:
        response = await self._client.get(f"/api/v1/organizations/{org_id}/members", headers=self.bearer_headers(token))
        return ResponseWrapper(response, TypeAdapter(list[MemberDTO]))

    async def update_member_roles(
        self,
        org_id: int,
        member_id: int,
        data: MemberRolesUpdateDTO | dict[str, Any],
        token: str | None = None,
    ) -> ResponseWrapper[MemberDTO]:
        response = await self._client.put(
            f"/api/v1/organizations/{org_id}/members/{member_id}/roles",
            json=self.to_json(data),
            headers=self.bearer_headers(token),
        )
        return ResponseWrapper(response, MemberDTO)

    async def remove_member(
        self, org_id: int, member_id: int, token: str | None = None
    ) -> ResponseWrapper[SuccessOperationDTO]:
        response = await self._client.delete(
            f"/api/v1/organizations/{org_id}/members/{member_id}", headers=self.bearer_headers(token)
        )
        return ResponseWrapper(response, SuccessOperationDTO)
