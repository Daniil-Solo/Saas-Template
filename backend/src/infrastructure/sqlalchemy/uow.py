from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction, async_sessionmaker

from src.infrastructure.dao.invitations.interface import InvitationsDAO
from src.infrastructure.dao.members.interface import MembersDAO
from src.infrastructure.dao.organizations.interface import OrganizationsDAO
from src.infrastructure.dao.roles.interface import RolesDAO
from src.infrastructure.dao.users.interface import UsersDAO


class Connection:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def transaction(self) -> AsyncSessionTransaction:
        """Атомарный блок внутри соединения (SAVEPOINT): при ошибке откатываются только его изменения."""
        return self._session.begin_nested()


class UnitOfWork:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        users_dao_factory: Callable[[AsyncSession], UsersDAO],
        organizations_dao_factory: Callable[[AsyncSession], OrganizationsDAO],
        members_dao_factory: Callable[[AsyncSession], MembersDAO],
        roles_dao_factory: Callable[[AsyncSession], RolesDAO],
        invitations_dao_factory: Callable[[AsyncSession], InvitationsDAO],
    ) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        # dao factory
        self._users_dao_factory = users_dao_factory
        self._organizations_dao_factory = organizations_dao_factory
        self._members_dao_factory = members_dao_factory
        self._roles_dao_factory = roles_dao_factory
        self._invitations_dao_factory = invitations_dao_factory
        # dao
        self._users: UsersDAO | None = None
        self._organizations: OrganizationsDAO | None = None
        self._members: MembersDAO | None = None
        self._roles: RolesDAO | None = None
        self._invitations: InvitationsDAO | None = None

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[Connection, None]:
        """Открывает сессию; при успешном выходе коммитит изменения, при ошибке откатывает."""
        session = self._session_factory()
        self._session = session
        try:
            yield Connection(session)
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
        finally:
            self._users = None
            self._organizations = None
            self._members = None
            self._roles = None
            self._invitations = None
            self._session = None
            await session.close()

    def _get_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("DAO доступны только внутри `async with uow.connection()`")
        return self._session

    @property
    def users(self) -> UsersDAO:
        if self._users is None:
            self._users = self._users_dao_factory(self._get_session())
        return self._users

    @property
    def organizations(self) -> OrganizationsDAO:
        if self._organizations is None:
            self._organizations = self._organizations_dao_factory(self._get_session())
        return self._organizations

    @property
    def members(self) -> MembersDAO:
        if self._members is None:
            self._members = self._members_dao_factory(self._get_session())
        return self._members

    @property
    def roles(self) -> RolesDAO:
        if self._roles is None:
            self._roles = self._roles_dao_factory(self._get_session())
        return self._roles

    @property
    def invitations(self) -> InvitationsDAO:
        if self._invitations is None:
            self._invitations = self._invitations_dao_factory(self._get_session())
        return self._invitations
