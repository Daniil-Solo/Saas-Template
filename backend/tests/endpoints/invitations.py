from typing import Any

from pydantic import TypeAdapter

from src.dto.common import SuccessOperationDTO
from src.dto.invitations import InvitationCreatedDTO, InvitationCreateDTO, InvitationDTO, InvitationPreviewDTO
from src.dto.organizations import OrganizationDTO
from tests.endpoints.base import BaseEndpoints
from tests.endpoints.response import ResponseWrapper


class InvitationsEndpoints(BaseEndpoints):
    async def create(
        self, org_id: int, data: InvitationCreateDTO | dict[str, Any], token: str | None = None
    ) -> ResponseWrapper[InvitationCreatedDTO]:
        response = await self._client.post(
            f"/api/v1/organizations/{org_id}/invitations",
            json=self.to_json(data),
            headers=self.bearer_headers(token),
        )
        return ResponseWrapper(response, InvitationCreatedDTO)

    async def get_all(self, org_id: int, token: str | None = None) -> ResponseWrapper[list[InvitationDTO]]:
        response = await self._client.get(
            f"/api/v1/organizations/{org_id}/invitations", headers=self.bearer_headers(token)
        )
        return ResponseWrapper(response, TypeAdapter(list[InvitationDTO]))

    async def revoke(
        self, org_id: int, invitation_id: int, token: str | None = None
    ) -> ResponseWrapper[SuccessOperationDTO]:
        response = await self._client.delete(
            f"/api/v1/organizations/{org_id}/invitations/{invitation_id}", headers=self.bearer_headers(token)
        )
        return ResponseWrapper(response, SuccessOperationDTO)

    async def preview(self, invitation_token: str, token: str | None = None) -> ResponseWrapper[InvitationPreviewDTO]:
        response = await self._client.get(f"/api/v1/invitations/{invitation_token}", headers=self.bearer_headers(token))
        return ResponseWrapper(response, InvitationPreviewDTO)

    async def accept(self, invitation_token: str, token: str | None = None) -> ResponseWrapper[OrganizationDTO]:
        response = await self._client.post(
            f"/api/v1/invitations/{invitation_token}/accept", headers=self.bearer_headers(token)
        )
        return ResponseWrapper(response, OrganizationDTO)
