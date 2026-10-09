from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction, async_sessionmaker

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
    ) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        # dao factory
        self._users_dao_factory = users_dao_factory
        # dao
        self._users: UsersDAO | None = None

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
