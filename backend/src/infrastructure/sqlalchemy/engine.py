from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.settings import DBSettings


async def init_engine(settings: DBSettings) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(settings.async_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        await engine.dispose()


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
