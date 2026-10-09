# AGENTS.md

## О проекте

Здесь будет краткая информация о проекте


## Технологический стек

- Веб-фреймворк и сервер: fastapi, uvicorn
- Статические анализаторы: ruff, mypy
- Консольные утилиты: click (asyncclick), rich
- Инъекция зависимостей: dependency-injector
- Базы данных: sqlalchemy (Core), alembic, asyncpg (основной), psycopg2-binary (миграции)
- LLM-пайплайн: openai, jinja2 (шаблон промпта), tiktoken
- Конфигурация: pydantic-settings
- Аутентификация: pyjwt
- Хранилище: boto3 (S3)
- Уведомления: maileroo (сервис отправки писем), jinja2 (шаблон письма)
- Rate limiting: redis
- Логирование: structlog

## Структура проекта

- alembic/ - миграции базы данных
- docs - документация
  - architecture/ - основные mermaid-диаграммы проекта
    - architecture.md - C4-диаграмма компонентов системы (уровень контейнеров)
    - data_model.md - ER-диаграмма (модель данных, 12 сущностей)
  - usecases/ - текстовое описание фичей с предложениями по реализации
  - development.md - инструкции для запуска проекта и линтеров
- src - весь исходный код проекта
  - application - сервисы бизнес-логики
    - auth/ - сервис аутентификации (login, register)
    - health/ - сервис проверки здоровья
    - users/ - сервисы для работы с пользователями
    - exceptions.py - кастомные исключения (ApplicationError и др.)
  - di/ - контейнер dependency-injector
    - container.py - объявление всех зависимостей
  - dto - Data Transfer Objects для API и Service слоев
    - auth/ - DTO для аутентификации (UserLoginDTO, TokenDTO, UserRegisterDTO)
    - users/ - DTO для пользователей (UserCreateDTO, UserDTO)
    - common.py - базовые DTO (BaseDTO, SuccessOperationDTO)
  - constants/ - константы и перечисления для сущностей
    - users.py - enums для User (UserType)
  - infrastructure - коннекторы к базе данных и внешним сервисам
    - auth/ - утилиты аутентификации (JWT, хеширование паролей SHA256+salt)
      - jwt.py - создание и декодирование JWT
      - password.py - хеширование паролей
    - dao/ - Data Access Object для работы с БД
      - users/ - DAO пользователей
    - llm/ - инфраструктура для работы с LLM
      - base.py - BaseLLM, Message, Answer
      - openai_like.py - OpenAI-совместимый клиент
    - sqlalchemy/ - модели и таблицы БД
      - models.py - все таблицы SQLAlchemy Core
      - engine.py - асинхронный engine и session factory
      - uow.py - UnitOfWork, агрегация всех DAO для одной сессии
    - storage/ - хранилище S3
      - interface.py - абстрактный интерфейс
      - s3.py - S3 storage для решений
    - ai/ - AI инфраструктура
      - llm/ - LLM интерфейс и реализации
      - prompt_builder/ - построитель промптов (jinja2)
    - email_sender/ - отправка email
      - interface.py - абстрактный интерфейс
      - maileroo.py - реализация через Maileroo
    - email_templater/ - шаблоны email
      - interface.py - абстрактный интерфейс
      - jinja2.py - реализация через Jinja2
    - redis/ - Redis клиент
  - interfaces - различные точки входа в приложение
    - api - содержит эндпоинты API
      - v1/ - эндпоинты версии v1
        - auth/ - аутентификация (POST /api/v1/auth/login, POST /api/v1/auth/register)
        - users/ - управление пользователями (GET/POST /api/v1/users/*)
      - internal/ - внутренние эндпоинты
        - health.py - GET /api/internal/health
      - app.py - точка входа в приложение с объявлением FastAPI
      - dependencies.py - зависимости для FastAPI (get_current_user)
      - error_status_mapping.py - маппинг ошибок из бизнес-слоя на HTTP-коды
    - cli - содержит команды для запуска
    - tasks - фоновые задачи (заглушка)
  - settings/ - настройки

## Таблицы БД (SQLAlchemy Core)

1. users - пользователи


## Архитектурные слои

Проект использует слоистую архитектуру:

1. **Interfaces** - точка входа (API, CLI)
2. **Application** - бизнес-логика
3. **Infrastructure** - реализация доступа к данным и внешним сервисам
4. **DTO** - объекты передачи данных между слоями

## Дополнительные сведения

- `docs/development.md` - инструкции для запуска проекта, линтеров, миграций
- Все DAO реализуют паттерн Repository через SQLAlchemy Core
- UnitOfWork управляет сессиями и транзакциями
- DI-контейнер связывает все зависимости

## Важно

- Отвечай всегда на русском языке
- Для запуска команд всегда используй: `uv run ...`
- Для добавления библиотек в проект используй: `uv add ...` вместо прямого добавления в pyproject.toml
- Для полей DTO всегда указывай описание и возможную валидацию: `Field(description="...")`
- SQLAlchemy используется в режиме Core (императивные таблицы), не ORM; запросы в DAO также составляются с помощью Core
- Всегда реализуй эндпоинты, dao, сервисные функции по аналогии с уже существующими
- Название сервисных функций в application слое формируется без указания сущности, поскольку из файла application/{entities}/{entity}.py итак понятно к какой сущности относится функция
- Никогда не пытайся запустить сам тесты, а также любой Docker-контейнер
- Не пиши код alembic-миграции вручную, вызывай команду `uv run alembic ...`
- Никогда не используй импорты внутри функций, методов. Импорты должны быть строго в начале файла

## Флоу реализации эндпоинта, сервисной функции (application), DAO, DTO и SQLAlchemy-модели

### Создание SQLALchemy-модели

Новая модель добавляется в `src/infrastructure/sqlalchemy/models.py`

```python
entities_table = sa.Table(
    "entities",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "other_entities_id",
        sa.Integer,
        sa.ForeignKey("workspaces.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    ),
    sa.Column("status", sa.Enum(EntityStatusEnum, name="entities_status"), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.CheckConstraint("status IN ('VALUE_1', 'VALUE_2')", name="chk_status"),
)
```

EntityStatusEnum задается в Enums `src/constants/entities.py`

### DTO - Data Transfer Object

DTO добавляется в `src/dto/entities/entities.py`
```python
from src.dto.common import BaseDTO
from pydantic import Field

class EntityCreateDTO(BaseDTO):
    status: EntityStatusEnum = Field(description="Статус сущности")

class EntityUpdateDTO(EntityCreateDTO):
    pass

class EntityResponseDTO(EntityCreateDTO):
    id: int = Field(description="ID сущности")
    created_at: datetime.datetime = Field(description="Дата создания")
```

### DAO - Data Access Object

Потом создается интерфейс для доступа к данным в `src/infrastructure/dao/entities/interface.py`
```python
from abc import ABC, abstractmethod


class EntitiesDAO(ABC):
    @abstractmethod
    async def create(self, data: EntityCreateDTO) -> EntityResponseDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> EntityResponseDTO:
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity_id: int, data: EntityUpdateDTO) -> EntityResponseDTO:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, entity_id: int) -> None:
        raise NotImplementedError
```
При необходимости могут быть добавлены дополнительные методы


После этого создаем реализацию интерфейса на SQLALChemy в `src/infrastructure/dao/entities/sqlalchemy.py`
```python
import sqlalchemy as sa
from src.infrastructure.dao.entities.interface import EntitiesDAO
from src.dto.entities import EntityCreateDTO, EntityUpdateDTO, EntityResponseDTO

class SQLAlchemyEntitiesDAO(EntitiesDAO):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: EntityCreateDTO) -> EntityResponseDTO:
        query = sa.insert(entities_table).values(**data.model_dump(by_alias=True)).returning(entities_table)
        result = await self.session.execute(query)
        row = result.fetchone()
        if row is None:
            raise EntityNotFoundError(message="Сущность не создана")
        return EntityResponseDTO.model_validate(row)

    async def get_by_id(self, entity_id: int) -> EntityResponseDTO:
        query = sa.select(entities_table).where(entities_table.c.id == entity_id)
        result = await self.session.execute(query)
        row = result.fetchone()
        if row is None:
            raise EntityNotFoundError(message="Сущность не найдена")
        return EntityResponseDTO.model_validate(row)

    async def update(self, entity_id: int, data: EntityUpdateDTO) -> EntityResponseDTO:
        query = (
            sa.update(entities_table)
            .where(entities_table.c.id == entity_id)
            .values(**data.model_dump(by_alias=True))
            .returning(entities_table)
        )
        result = await self.session.execute(query)
        row = result.fetchone()
        if row is None:
            raise EntityNotFoundError(message="Сущность не найдена")
        return EntityResponseDTO.model_validate(row)

    async def delete(self, entity_id: int) -> None:
        query = sa.delete(entities_table).where(entities_table.c.id == entity_id)
        await self.session.execute(query)
```

Добавляем dao в DI-контейнер в `src/di/container.py`
```python
class Container(containers.DeclarativeContainer):
    ...
    
    entities_dao = providers.Factory(lambda: SQLAlchemyEntitiesDAO)

    uow = providers.Factory(
        UnitOfWork,
        ...
        entities_dao_factory=entities_dao,
    )
```

И добавляем dao в UnitOfWork в `src/infrastructure/sqlalchemy/uow.py`
```python
class UnitOfWork:
    def __init__(
        self,
        ...
        entities_dao_factory: Callable[[AsyncSession], EntitiesDAO],
    ) -> None:
        ...
        # dao factory
        ...
        self._entities_dao_factory = entities_dao_factory
        # dao
        ...
        self._entities: EntitiesDAO | None = None

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[Connection, None]:
        ...
        finally:
            if self._session is not None:
                ...
                self._entities = None
    
    ...
            
    @property
    def entities(self) -> EntitiesDAO:
        if self._entities is None:
            self._entities = self._entities_dao_factory(self._session)
        return self._entities
```

### Application Layer
Создаем сервисные функции в `src/application/entities/entities.py`

```python
from dependency_injector import inject
from dependency_injector.wiring import Provide

@inject
async def create_entity(
    data: EntityCreateDTO,
    user: ShortUserDTO,
    uow: UnitOfWork = Provide[Container.uow],
) -> WorkspaceResponseDTO:
    async with uow.connection():
        entity = await uow.entities.create(data)
        return entity
```

Если в сервисной функции используется последовательное обновление нескольких записей, то такие операции необходимо дополнительно обернуть в транзакцию:
```python
async with uow.connection() as conn, conn.transaction():
    await operation_1()
    await operation_2()
```

И добавляем связывание в DI-контейнере `src/di/container.py`
```python
async def init_container() -> Container:
    container = Container()
    container.wire(
        packages=[
          ...
            "src.application.entities",
        ]
    )
    await container.init_resources()
    return container
```

### Endpoints
Эндпоинты добавляются в `src/interfaces/api/v1/entities/router.py`
```python
from fastapi import APIRouter, Depends
from src.interfaces.api.dependencies import get_current_user
from src.application.entities import create_entity

router = APIRouter(prefix="/entities", tags=["entities"])

@router.post("/", response_model=EntityResponseDTO)
async def create_workspace_endpoint(
    data: EntityCreateDTO,
    user: ShortUserDTO = Depends(get_current_user),
) -> EntityResponseDTO:
    return await create_entity(data, user)
```

Для операций, которые ничего не возвращают, например, удаление сущности, в качестве ответа возвращается SuccessOperationDTO(message="") из `src/dto/common.py`

И импортируем новый роутер в `src/interfaces/api/v1/__init__.py`
```python
from fastapi import APIRouter
from src.interfaces.api.v1.entities.router import router as entities_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])
...
v1_router.include_router(entities_router)

__all__ = ["v1_router"]
```

## Флоу тестирования эндпоинта

Для каждого эндпоинта создается отдельный файл с тестами (пример: `tests/interfaces/api/v1/users/test_create.py`)

```python
from fastapi import status
from httpx import AsyncClient, Response
import pytest_asyncio

from src.dto.users import UserCreateDTO, UserResponseDTO
from tests.factories.users import UserFactory
from tests.helpers.users import create_users


@pytest_asyncio.fixture()
def request_create_user(client: AsyncClient):
    async def inner(data: UserCreateDTO) -> Response:
        return await client.post("/api/v1/users", json=data.model_dump(by_alias=True))

    return inner


@pytest_asyncio.fixture()
def create_user(request_create_user):
    async def inner(data: UserCreateDTO) -> UserResponseDTO:
        response = await request_create_user(data)
        assert response.status_code == status.HTTP_200_OK
        return UserResponseDTO.model_validate_json(response.text)

    return inner


async def test__success(uow, create_user):
    data: UserCreateDTO = UserFactory.build()

    user = await create_user(data)
    assert user.email == data.email
    assert user.fullname == data.fullname
    assert not user.is_admin


async def test__failed__duplicated_email(uow, request_create_user):
    created_user = (await create_users(uow))[0]
    data: UserCreateDTO = UserFactory.build(email=created_user.email)

    response = await request_create_user(data)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["code"] == "user_email_exists"
```

Важно:
- Тест в качестве обязательной фикстуры всегда должен использовать uow или container (они инициализируют DI-контейнер для работы сервисных функций)
- Подготовка данных для создания объектов в БД должна осуществляться через Factory-классы
- Если в тестах повторяются какие-то операции, их следует вынести во вспомогательные функции
- Конвенция по наименованию тестов: test__success - успешный, test__failed__not_admin - проваленный тест
- Никогда не размещай обращение к SQL внутри сервисных функций, всегда создавай для этого дополнительные методы DAO
- Для тестов в которых возвращается список моделей используй синтаксис: `TypeAdapter(list[EntityDTO]).validate_json(response.text)`