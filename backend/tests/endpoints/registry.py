from httpx import AsyncClient

from tests.endpoints.auth import AuthEndpoints
from tests.endpoints.internal import InternalEndpoints
from tests.endpoints.invitations import InvitationsEndpoints
from tests.endpoints.notifications import NotificationsEndpoints
from tests.endpoints.organizations import OrganizationsEndpoints
from tests.endpoints.roles import PermissionsEndpoints, RolesEndpoints
from tests.endpoints.users import UsersEndpoints


class EndpointRegistry:
    """Единая точка вызова эндпоинтов в тестах: `api.auth.login(...)`, `api.users.me(token)`.

    Новая группа эндпоинтов добавляется классом в `tests/endpoints/` и свойством здесь.
    """

    def __init__(self, client: AsyncClient) -> None:
        self._auth = AuthEndpoints(client)
        self._users = UsersEndpoints(client)
        self._internal = InternalEndpoints(client)
        self._organizations = OrganizationsEndpoints(client)
        self._invitations = InvitationsEndpoints(client)
        self._roles = RolesEndpoints(client)
        self._permissions = PermissionsEndpoints(client)
        self._notifications = NotificationsEndpoints(client)

    @property
    def auth(self) -> AuthEndpoints:
        return self._auth

    @property
    def users(self) -> UsersEndpoints:
        return self._users

    @property
    def internal(self) -> InternalEndpoints:
        return self._internal

    @property
    def organizations(self) -> OrganizationsEndpoints:
        return self._organizations

    @property
    def invitations(self) -> InvitationsEndpoints:
        return self._invitations

    @property
    def roles(self) -> RolesEndpoints:
        return self._roles

    @property
    def permissions(self) -> PermissionsEndpoints:
        return self._permissions

    @property
    def notifications(self) -> NotificationsEndpoints:
        return self._notifications
