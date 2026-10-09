from httpx import AsyncClient

from tests.endpoints.auth import AuthEndpoints
from tests.endpoints.internal import InternalEndpoints
from tests.endpoints.users import UsersEndpoints


class EndpointRegistry:
    """Единая точка вызова эндпоинтов в тестах: `api.auth.login(...)`, `api.users.me(token)`.

    Новая группа эндпоинтов добавляется классом в `tests/endpoints/` и свойством здесь.
    """

    def __init__(self, client: AsyncClient) -> None:
        self._auth = AuthEndpoints(client)
        self._users = UsersEndpoints(client)
        self._internal = InternalEndpoints(client)

    @property
    def auth(self) -> AuthEndpoints:
        return self._auth

    @property
    def users(self) -> UsersEndpoints:
        return self._users

    @property
    def internal(self) -> InternalEndpoints:
        return self._internal
