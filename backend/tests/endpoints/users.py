from src.dto.users import UserDTO
from tests.endpoints.base import BaseEndpoints
from tests.endpoints.response import ResponseWrapper


class UsersEndpoints(BaseEndpoints):
    async def me(self, token: str | None = None, scheme: str = "Bearer") -> ResponseWrapper[UserDTO]:
        """token=None - запрос без заголовка Authorization."""
        response = await self._client.get("/api/v1/users/me", headers=self.bearer_headers(token, scheme))
        return ResponseWrapper(response, UserDTO)
