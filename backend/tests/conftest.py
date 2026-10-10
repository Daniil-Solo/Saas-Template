from collections.abc import AsyncGenerator, Generator
import logging

from alembic.config import Config
import asyncpg
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy import text

from alembic import command
from src.di.container import Container, init_container, shutdown_container
from src.infrastructure.sqlalchemy.models import metadata
from src.infrastructure.sqlalchemy.uow import UnitOfWork
from src.interfaces.api.app import create_app
from src.settings import DBSettings, get_settings
from tests.endpoints.registry import EndpointRegistry
from tests.fakes.fakes import FakeEmailSender, FakeTaskQueue

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_database_name() -> Generator[str, None, None]:
    """Создает отдельную БД на том же сервере и направляет на нее настройки DB_NAME. Основная БД не затрагивается."""
    main_settings = DBSettings()  # type: ignore[call-arg]
    test_db_name = f"test_{main_settings.name}"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("DB_NAME", test_db_name)
    get_settings.cache_clear()
    yield test_db_name
    monkeypatch.undo()
    get_settings.cache_clear()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def run_migrations(test_database_name: str) -> AsyncGenerator[None, None]:
    # Подключаемся к основной БД только чтобы создать и удалить тестовую
    main_settings = DBSettings(name="postgres")  # type: ignore[call-arg]
    conn = await asyncpg.connect(
        host=main_settings.host,
        port=main_settings.port,
        user=main_settings.user,
        password=main_settings.password,
        database=main_settings.name,
    )
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{test_database_name}" WITH (FORCE)')
        await conn.execute(f'CREATE DATABASE "{test_database_name}"')
        logger.info("Test database %s created", test_database_name)

        # alembic/env.py берет настройки из окружения, где DB_NAME уже указывает на тестовую БД
        command.upgrade(Config("alembic.ini"), "head")

        yield
    finally:
        await conn.execute(f'DROP DATABASE IF EXISTS "{test_database_name}" WITH (FORCE)')
        await conn.close()
        logger.info("Test database %s dropped", test_database_name)


@pytest.fixture
def task_queue() -> FakeTaskQueue:
    return FakeTaskQueue()


@pytest.fixture
def email_sender() -> FakeEmailSender:
    return FakeEmailSender()


@pytest_asyncio.fixture(scope="function")
async def container(
    run_migrations: None, task_queue: FakeTaskQueue, email_sender: FakeEmailSender
) -> AsyncGenerator[Container, None]:
    container = await init_container()
    # Очередь и отправка писем в тестах всегда подменены: письма не уходят, Redis не используется
    container.task_queue.override(providers.Object(task_queue))
    container.email_sender.override(providers.Object(email_sender))

    engine = await container.engine()
    table_names = ", ".join(table.name for table in metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))

    try:
        yield container
    finally:
        await shutdown_container(container)


@pytest_asyncio.fixture(scope="function")
async def uow(container: Container) -> UnitOfWork:
    # uow зависит от async-ресурса (engine), поэтому провайдер возвращает awaitable
    return await container.uow()


@pytest_asyncio.fixture(scope="function")
async def api(container: Container) -> AsyncGenerator[EndpointRegistry, None]:
    """Вызов эндпоинтов: `api.auth.login(...)`. Зависит от container, поэтому DI всегда инициализирован."""
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield EndpointRegistry(client)
