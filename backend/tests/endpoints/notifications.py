from typing import Any

from fastapi import status
from pydantic import TypeAdapter

from src.dto.emails import EmailEnqueuedDTO, EmailSendRequestDTO, EmailTemplateInfoDTO
from tests.endpoints.base import BaseEndpoints
from tests.endpoints.response import ResponseWrapper


class NotificationsEndpoints(BaseEndpoints):
    async def send_email(
        self, data: EmailSendRequestDTO | dict[str, Any], token: str | None = None
    ) -> ResponseWrapper[EmailEnqueuedDTO]:
        response = await self._client.post(
            "/api/v1/notifications/email", json=self.to_json(data), headers=self.bearer_headers(token)
        )
        return ResponseWrapper(response, EmailEnqueuedDTO, success_status=status.HTTP_202_ACCEPTED)

    async def templates(self, token: str | None = None) -> ResponseWrapper[list[EmailTemplateInfoDTO]]:
        response = await self._client.get("/api/v1/notifications/templates", headers=self.bearer_headers(token))
        return ResponseWrapper(response, TypeAdapter(list[EmailTemplateInfoDTO]))
