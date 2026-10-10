# AGENTS.md

## О проекте

Это backend-шаблон для быстрого старта приложений (в том числе microSaaS). Репозиторий содержит общий рабочий код, который нужен почти любому приложению: аутентификация, пользователи, работа с БД, миграции, DI, хранилище S3, отправка email, rate limiting, LLM-инфраструктура, логирование, healthcheck, CLI.

Предметная логика конкретного продукта добавляется поверх шаблона: новые сущности, сервисы и эндпоинты создаются по флоу из раздела «Флоу реализации» ниже. Существующий общий код (auth, users, infrastructure) расширяй, а не переписывай, если пользователь явно не попросил об обратном.

Описание конкретного продукта (если оно есть) лежит в `../docs/usecases/` (общие для backend и frontend). Перед реализацией новой фичи проверь, нет ли там описания.


## Технологический стек

- Веб-фреймворк и сервер: fastapi, uvicorn
- Статические анализаторы: ruff, mypy
- Консольные утилиты: click (asyncclick), rich
- Инъекция зависимостей: dependency-injector
- Базы данных: sqlalchemy (Core), alembic, asyncpg (основной), psycopg2-binary (миграции)
- LLM-пайплайн: openai, jinja2 (шаблон промпта), tiktoken
- Конфигурация: pydantic-settings
- Метрики и ошибки: prometheus-client, sentry-sdk
- Аутентификация: pyjwt, argon2-cffi (хеширование паролей)
- Хранилище: boto3 (S3)
- Фоновые задачи: arq (очередь на Redis)
- Письма: коннекторы `smtp` (aiosmtplib), `maileroo` (httpx) и `console` (лог, по умолчанию); шаблоны писем - jinja2
- Redis: очередь задач, rate limiting
- Логирование: structlog
- Тесты: pytest, pytest-asyncio, httpx, factory-boy


## Структура проекта

Дерево ниже описывает ключевые директории. Актуальное содержимое смотри в файловой системе, а не полагайся на этот список как на исчерпывающий.

- alembic/ - миграции базы данных
- docs/ - документация
  - architecture/ - mermaid-диаграммы проекта
    - architecture.md - диаграммы компонентов системы (в том числе C4, уровень контейнеров)
    - data_model.md - ER-диаграмма (модель данных)
  - development.md - запуск проекта, dev-окружение (Docker), линтеры, миграции, тесты
- src/ - весь исходный код проекта
  - application/ - сервисы бизнес-логики
    - auth/ - сервис аутентификации (login, register)
    - health/ - сервис проверки здоровья
    - users/ - сервисы для работы с пользователями
    - organizations/ - организации (`organizations.py`) и участники (`members.py`)
    - roles/ - роли (создание и изменение - только администратор)
    - invitations/ - приглашения: создание, отзыв, просмотр и принятие по токену
    - notifications/ - письма (`emails.py`): отправка приветствия и приглашения; вызываются задачами воркера
    - permissions/ - перечень прав
    - exceptions.py - кастомные исключения (ApplicationError и др.)
  - di/ - контейнер dependency-injector
    - container.py - объявление всех зависимостей
  - dto/ - Data Transfer Objects для API и Service слоев
    - auth/ - DTO для аутентификации (UserLoginDTO, TokenDTO, UserRegisterDTO)
    - users/ - DTO для пользователей (UserCreateDTO, UserDTO)
    - organizations/, roles/, invitations/ - DTO организаций, ролей и приглашений
    - emails/ - контексты шаблонов писем и `EmailMessage`; tasks/ - payload фоновых задач
    - common.py - базовые DTO (BaseDTO, SuccessOperationDTO)
  - constants/ - константы и перечисления для сущностей
    - emails.py - `EmailTemplate` (перечень шаблонов писем); tasks.py - `TaskName` (имена фоновых задач)
    - permissions.py - `Permission` (права ролей)
    - invitations.py - `InvitationStatus` (хранимый) и `InvitationDisplayStatus` (для API)
  - infrastructure/ - коннекторы к базе данных и внешним сервисам
    - auth/ - утилиты аутентификации
      - jwt.py - создание и декодирование JWT
      - password.py - хеширование паролей (argon2)
    - dao/ - Data Access Object для работы с БД
      - users/ - DAO пользователей
    - sqlalchemy/ - модели и таблицы БД
      - models.py - все таблицы SQLAlchemy Core
      - engine.py - асинхронный engine и session factory
      - uow.py - UnitOfWork, агрегация всех DAO для одной сессии
    - storage/ - хранилище S3
      - interface.py - абстрактный интерфейс
      - s3.py - реализация через S3
    - ai/ - AI инфраструктура
      - llm/ - LLM интерфейс и реализации (base.py: BaseLLM, Message, Answer; openai_like.py: OpenAI-совместимый клиент)
      - prompt_builder/ - построитель промптов (jinja2)
    - email_sender/ - коннекторы отправки email (interface.py: `EmailSender`; exceptions.py: `EmailTemporaryError`, `EmailPermanentError`; smtp.py, maileroo.py, console.py)
    - email_templater/ - рендер писем (interface.py: `EmailTemplater`; jinja2.py; templates/: `_layout.*.j2` и папка на каждое письмо)
    - queue/ - очередь фоновых задач (interface.py: `TaskQueue`; arq.py)
    - redis/ - Redis клиент
    - observability/ - логирование (logging.py, structlog), метрики Prometheus (metrics.py), Sentry (sentry.py), контекст запроса (context.py)
  - interfaces/ - различные точки входа в приложение
    - api/ - эндпоинты API
      - v1/ - эндпоинты версии v1
        - auth/ - аутентификация (POST /api/v1/auth/login, POST /api/v1/auth/register)
        - users/ - управление пользователями (GET/POST /api/v1/users/*)
        - organizations/ - организации, участники и приглашения организации (/api/v1/organizations/*)
        - roles/, permissions/, invitations/ - роли, права, принятие приглашений по токену
        - notifications/ - только админ: POST /api/v1/notifications/email (поставить письмо по типу шаблона и payload), GET /api/v1/notifications/templates (каталог)
      - internal/ - внутренние эндпоинты
        - health.py - GET /api/internal/health
        - metrics.py - GET /api/internal/metrics (метрики Prometheus, вне OpenAPI)
      - app.py - точка входа в приложение с объявлением FastAPI
      - middleware.py - ASGI-middleware: X-Request-ID, запись `http_request` в логе, HTTP-метрики
      - dependencies.py - зависимости для FastAPI (get_current_user, get_current_admin, require_permission)
      - error_status_mapping.py - маппинг ошибок из бизнес-слоя на HTTP-коды
    - cli/ - команды (например, `email_preview` - предпросмотр писем)
    - tasks/ - воркер arq: `worker.py` (`WorkerSettings`), задачи по областям (`emails.py`)
  - settings/ - настройки: группы (`DBSettings`, `AuthSettings`, `RedisSettings`, `EmailSettings`, `SmtpSettings`, `MailerooSettings`, `LoggingSettings`, `MetricsSettings`, `SentrySettings` и др.) и единый `Settings` с `get_settings()`
- tests/ - тесты (структура зеркалит `src/`)
  - endpoints/ - обертки над эндпоинтами для тестов: `EndpointRegistry` (фикстура `api`), классы групп (`AuthEndpoints`, `UsersEndpoints`, ...), `ResponseWrapper`
  - interfaces/api/v1/{entities}/ - тесты эндпоинтов, один файл на эндпоинт
  - factories/ - Factory-классы для генерации данных
  - helpers/ - вспомогательные функции для тестов (создание данных в БД, токены)
  - conftest.py - фикстуры (container, uow, api, тестовая БД, миграции)

## Таблицы БД (SQLAlchemy Core)

Источник истины - ER-диаграмма `docs/architecture/data_model.md`; модели в `src/infrastructure/sqlalchemy/models.py` должны ей соответствовать.

1. users - пользователи
2. organizations - организации (создатель - `created_by_id`)
3. organization_members - участники организаций
4. roles - глобальные роли (создаёт только администратор системы)
5. role_permissions - права роли (строковый код из `Permission`)
6. member_roles - роли участников
7. invitations - приглашения в организацию (в БД только хеш токена)
8. invitation_roles - роли приглашений


## Документация - источник истины

Диаграммы в `docs/architecture/` (`architecture.md`, `data_model.md`) и общая для проектов схема развертывания `../docs/deployment.md` - источник истины и отправная точка разработки. Код следует за диаграммами, а не наоборот.

- Перед реализацией фичи прочитай релевантные диаграммы и описание в `../docs/usecases/`
- Если фича меняет состав системы (новый контейнер, воркер, внешний сервис), модель данных (таблица, поле, связь, enum) или развертывание, то СНАЧАЛА обнови соответствующую диаграмму, и только потом пиши код, миграции и конфигурацию
- Если код и диаграмма расходятся, не подгоняй молча ни одно под другое: сообщи пользователю о расхождении и предложи, что менять
- В конце задачи убедись, что диаграммы соответствуют результату

## Архитектурные слои

Проект использует слоистую архитектуру. Зависимости направлены только вниз:

1. **Interfaces** - точки входа (API, CLI, tasks). Только валидация входа, вызов сервисной функции и формирование ответа. Бизнес-логики здесь нет
2. **Application** - бизнес-логика. Работает с БД только через DAO из UnitOfWork, с внешними сервисами - только через интерфейсы infrastructure
3. **Infrastructure** - реализация доступа к данным и внешним сервисам. Каждая внешняя зависимость описывается абстрактным интерфейсом (`interface.py`) и конкретной реализацией
4. **DTO** - объекты передачи данных между слоями (сквозной слой, доступен всем)

Правила зависимостей:
- Application не импортирует ничего из `interfaces`
- Infrastructure не импортирует ничего из `application` и `interfaces`
- Бизнес-ошибки - наследники `ApplicationError` из `src/application/exceptions.py`; их превращение в HTTP-коды происходит только в `src/interfaces/api/error_status_mapping.py`. В application и infrastructure `HTTPException` не используется

## Дополнительные сведения

- `docs/development.md` - всё про локальную разработку: запуск проекта, dev-окружение (Docker), установка зависимостей, линтеры, миграции, тесты
- Все DAO реализуют паттерн Repository через SQLAlchemy Core
- UnitOfWork управляет сессиями и транзакциями
- DI-контейнер связывает все зависимости

## Важно

- Отвечай всегда на русском языке
- Все команды проекта (ruff, mypy, alembic, pytest, скрипты) выполняются внутри docker-контейнера, команды описаны в `docs/development.md`. На хосте зависимости не устанавливаются
- Для добавления библиотек в проект используй: `uv add ...` вместо прямого добавления в pyproject.toml, чтобы lock-файл оставался согласованным
- Для полей DTO всегда указывай описание и возможную валидацию: `Field(description="...")` (описания попадают в OpenAPI-схему)
- SQLAlchemy используется в режиме Core (императивные таблицы), не ORM; запросы в DAO также составляются с помощью Core
- Всегда реализуй эндпоинты, dao, сервисные функции по аналогии с уже существующими
- Название сервисных функций в application слое формируется без указания сущности (`create`, `get_by_id`, `update`, `delete`), поскольку из файла `application/{entities}/{entity}.py` и так понятно, к какой сущности относится функция. В роутерах сервис импортируется как модуль: `from src.application.entities import entities as entities_service`, вызов - `entities_service.create(...)`
- Никогда не размещай обращение к SQL внутри сервисных функций, всегда создавай для этого дополнительные методы DAO
- Не пиши код alembic-миграции вручную, генерируй её командой `docker compose exec app alembic revision --autogenerate -m "..."`, затем проверь результат и не переписывай его без необходимости. Накатывать миграции на базу не нужно, если пользователь об этом не просил
- Никогда не используй импорты внутри функций, методов. Импорты должны быть строго в начале файла
- Не храни секреты и ключи в коде и в репозитории: все значения берутся из `src/settings/` (pydantic-settings), а новые переменные окружения добавляются в `.example.env`
- Не удаляй docker-тома (`down -v`) и не трогай основную БД вне миграций без явной просьбы пользователя: в ней лежат данные разработки

## Dev-окружение и проверки

Запуск проекта, dev-окружение (Docker), миграции, линтеры, тесты и добавление переменных окружения описаны в `docs/development.md`; не дублируй эти инструкции здесь.

Перед завершением задачи выполни форматирование, `ruff check` и `mypy` и исправь замечания. Если задача затрагивает эндпоинт, сервис или DAO, запусти относящиеся к ним тесты, а перед завершением - весь набор. В ответе сообщи, что запускалось и каков результат; если что-то не удалось запустить, скажи об этом прямо.

## Флоу реализации эндпоинта, сервисной функции (application), DAO, DTO и SQLAlchemy-модели

Порядок: обновить ER-диаграмму `docs/architecture/data_model.md` → модель и enum → DTO → DAO (интерфейс, реализация, DI, UoW) → сервис → роутер → тесты → миграция. Ниже `entities` - плейсхолдер названия сущности.

### Создание SQLAlchemy-модели

Новая модель добавляется в `src/infrastructure/sqlalchemy/models.py`

```python
entities_table = sa.Table(
    "entities",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "other_entity_id",
        sa.Integer,
        sa.ForeignKey("other_entities.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    ),
    sa.Column("status", sa.Enum(EntityStatusEnum, name="entities_status"), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
)
```

`EntityStatusEnum` задается в `src/constants/entities.py`. После добавления модели сгенерируй миграцию (см. раздел «Важно»).

### DTO - Data Transfer Object

DTO добавляется в `src/dto/entities/entities.py` (и реэкспортируется в `src/dto/entities/__init__.py`)
```python
import datetime

from pydantic import Field

from src.constants.entities import EntityStatusEnum
from src.dto.common import BaseDTO


class EntityCreateDTO(BaseDTO):
    status: EntityStatusEnum = Field(description="Статус сущности")


class EntityUpdateDTO(BaseDTO):
    status: EntityStatusEnum | None = Field(default=None, description="Статус сущности")


class EntityResponseDTO(EntityCreateDTO):
    id: int = Field(description="ID сущности")
    created_at: datetime.datetime = Field(description="Дата создания")
```

### DAO - Data Access Object

Потом создается интерфейс для доступа к данным в `src/infrastructure/dao/entities/interface.py`
```python
from abc import ABC, abstractmethod

from src.dto.entities import EntityCreateDTO, EntityResponseDTO, EntityUpdateDTO


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

После этого создаем реализацию интерфейса на SQLAlchemy в `src/infrastructure/dao/entities/sqlalchemy.py`
```python
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import EntityNotFoundError
from src.dto.entities import EntityCreateDTO, EntityResponseDTO, EntityUpdateDTO
from src.infrastructure.dao.entities.interface import EntitiesDAO
from src.infrastructure.sqlalchemy.models import entities_table


class SQLAlchemyEntitiesDAO(EntitiesDAO):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: EntityCreateDTO) -> EntityResponseDTO:
        query = sa.insert(entities_table).values(**data.model_dump()).returning(entities_table)
        result = await self.session.execute(query)
        return EntityResponseDTO.model_validate(result.one())

    async def get_by_id(self, entity_id: int) -> EntityResponseDTO:
        query = sa.select(entities_table).where(entities_table.c.id == entity_id)
        result = await self.session.execute(query)
        row = result.one_or_none()
        if row is None:
            raise EntityNotFoundError(message="Сущность не найдена")
        return EntityResponseDTO.model_validate(row)

    async def update(self, entity_id: int, data: EntityUpdateDTO) -> EntityResponseDTO:
        # exclude_unset: обновляются только поля, переданные клиентом
        values = data.model_dump(exclude_unset=True)
        if not values:
            return await self.get_by_id(entity_id)
        query = (
            sa.update(entities_table)
            .where(entities_table.c.id == entity_id)
            .values(**values)
            .returning(entities_table)
        )
        result = await self.session.execute(query)
        row = result.one_or_none()
        if row is None:
            raise EntityNotFoundError(message="Сущность не найдена")
        return EntityResponseDTO.model_validate(row)

    async def delete(self, entity_id: int) -> None:
        query = sa.delete(entities_table).where(entities_table.c.id == entity_id).returning(entities_table.c.id)
        result = await self.session.execute(query)
        if result.one_or_none() is None:
            raise EntityNotFoundError(message="Сущность не найдена")
```

Для `model_validate(row)` в `BaseDTO` должен быть включен `from_attributes=True`.

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
Создаем сервисные функции в `src/application/entities/entities.py` (названия без указания сущности)

```python
from dependency_injector.wiring import Provide, inject

from src.di.container import Container
from src.dto.common import SuccessOperationDTO
from src.dto.entities import EntityCreateDTO, EntityResponseDTO
from src.dto.users import UserDTO
from src.infrastructure.sqlalchemy.uow import UnitOfWork


@inject
async def create(
    data: EntityCreateDTO,
    user: UserDTO,  # текущий пользователь; используется для проверки прав доступа
    uow: UnitOfWork = Provide[Container.uow],
) -> EntityResponseDTO:
    async with uow.connection():
        return await uow.entities.create(data)
```

Если в сервисной функции используется последовательное изменение нескольких записей, то такие операции необходимо дополнительно обернуть в транзакцию:
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

from src.application.entities import entities as entities_service
from src.dto.common import SuccessOperationDTO
from src.dto.entities import EntityCreateDTO, EntityResponseDTO
from src.dto.users import UserDTO
from src.interfaces.api.dependencies import get_current_user

router = APIRouter(prefix="/entities", tags=["entities"])


@router.post("/", response_model=EntityResponseDTO)
async def create_entity_endpoint(
    data: EntityCreateDTO,
    user: UserDTO = Depends(get_current_user),
) -> EntityResponseDTO:
    return await entities_service.create(data, user)
```

Для операций, которые ничего не возвращают, например, удаление сущности, в качестве ответа возвращается `SuccessOperationDTO(message="")` из `src/dto/common.py`

И импортируем новый роутер в `src/interfaces/api/v1/__init__.py`
```python
from fastapi import APIRouter

from src.interfaces.api.v1.entities.router import router as entities_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])
...
v1_router.include_router(entities_router)

__all__ = ["v1_router"]
```

Если новые бизнес-ошибки должны возвращать особый HTTP-код, добавь их в `src/interfaces/api/error_status_mapping.py`.

## Фоновые задачи (arq)

В фон выносится действие, результат которого не нужен в ответе клиенту и которое может быть долгим или упасть без отмены основной операции (письма, обращения к внешним API, LLM). Если результат нужен сразу - это обычная сервисная функция.

Схема: сервис в `application` ставит задачу через `TaskQueue` → arq/Redis → воркер вызывает тонкую функцию-задачу в `interfaces/tasks/` → она вызывает сервисную функцию в `application`. Бизнес-логика живёт только в сервисной функции, поэтому её можно вызвать и из API, и из воркера, и из теста.

Правила:
- `arq` импортируется только в `infrastructure/queue/` и `interfaces/tasks/`. Application работает с интерфейсом `TaskQueue` из DI: `await queue.enqueue(TaskName.SEND_EMAIL, SendEmailDTO(to=user.email, template=EmailTemplate.WELCOME, context=welcome.model_dump(mode="json")), job_id=f"welcome-{user.id}")`
- Имя задачи - значение `TaskName` (`src/constants/tasks.py`), payload - pydantic DTO из `src/dto/tasks/`. В payload кладутся id сущностей, а не объекты и не данные, которые можно перечитать из БД. Секреты в payload запрещены; единственное исключение - одноразовый токен приглашения (в БД только его хеш), оно описано в плане фичи
- Ставь задачу только после коммита транзакции, то есть вне `async with uow.connection()`: иначе воркер может не найти запись. Redis считается доступным всегда: сбой постановки отдельно не обрабатывается
- Задача идемпотентна и сама перечитывает состояние из БД (приглашение могли отозвать, пока задача ждала в очереди) и пропускает работу, если она уже не нужна. Для защиты от дублей задавай детерминированный `job_id`
- Ретраи: временную ошибку (`*TemporaryError`) функция-задача превращает в `arq.Retry(defer=...)` с растущей паузой, `max_tries=5`; постоянную (`*PermanentError`) не повторяет и пишет `logger.error`. Новые внешние сервисы заводят такую же пару исключений
- В логи задач не попадают email, токены и тела писем (только `task`, `job_id`, `attempt`, шаблон)
- Воркер поднимает свой DI-контейнер, логирование и Sentry в `on_startup`, закрывает контейнер в `on_shutdown`. Запуск: `arq src.interfaces.tasks.worker.WorkerSettings`; новая задача добавляется в `WorkerSettings.functions`
- Постановка не атомарна с БД (outbox нет): задача, поставленная после коммита, может потеряться при падении Redis или процесса. Если для новой фичи потеря недопустима, обсуди с пользователем outbox до реализации
- В тестах `task_queue` в контейнере заменён на `FakeTaskQueue`: проверяй, что поставлена нужная задача с нужным payload; логику задачи тестируй прямым вызовом функции-задачи или сервисной функции

Новая фоновая задача: имя в `TaskName` → DTO payload → сервисная функция в `application/<область>/` → функция-задача в `interfaces/tasks/<область>.py` и регистрация в `WorkerSettings` → вызов `enqueue` из сервиса → тесты.

## Письма: коннекторы и шаблоны

Письма отправляются только из фоновых задач (см. выше), никогда из обработчика запроса.

**Коннекторы.** `EmailSender` (`infrastructure/email_sender/interface.py`) принимает `EmailMessage` и бросает `EmailTemporaryError` или `EmailPermanentError`. Реализация выбирается переменной `EMAIL_BACKEND` (`console` по умолчанию, `smtp`, `maileroo`) через `providers.Selector` в DI-контейнере. Новый коннектор: класс-наследник `EmailSender` → группа настроек со своим префиксом `EMAIL_<NAME>_` (поля необязательные) → проверка обязательных полей в валидаторе `Settings` (сообщение называет переменную) → значение в `EMAIL_BACKEND` и строка в `Selector` → переменные в оба `.example.env` → общий контрактный тест коннекторов. При `EMAIL_BACKEND=console` API и воркер пишут при старте предупреждение (`warning`), что письма не отправляются.

**Шаблоны.** `EmailTemplater.render(template, context)` возвращает `subject`, `html` и `text`. `template` - член `EmailTemplate` (`src/constants/emails.py`), `context` - pydantic DTO из `src/dto/emails/`; шаблон рендерится со `StrictUndefined`, поэтому пропущенная переменная - ошибка, а не пустое место. Файлы лежат в `infrastructure/email_templater/templates/`: общие `_layout.html.j2` и `_layout.txt.j2`, и папка `<template>/` с `subject.txt.j2`, `body.html.j2` (расширяет каркас), `body.txt.j2`.

Правила вёрстки HTML-писем: таблицы и inline-стили (без внешнего CSS, JS и картинок), ширина 560 px, акцентный цвет и шрифт - переменные в начале каркаса, кнопка + дублирующая ссылка под ней, скрытый прехедер, поддержка тёмной темы через `prefers-color-scheme`, обязательная текстовая версия. Любые пользовательские значения выводятся только с автоэкранированием.

**Универсальная отправка.** Любое письмо можно поставить в очередь через `notifications.send(to, template, context)` (рендер + отправка, выполняется задачей `SEND_EMAIL`) или через эндпоинт `POST /api/v1/notifications/email` (тело: `template`, `to`, `payload`, необязательный `idempotency_key`; ответ 202 с `job_id`). Каталог типов и JSON-схем payload - `GET /api/v1/notifications/templates`. Оба эндпоинта доступны только администратору системы (`get_current_admin`: 401 без токена, 403 не админу). Связь «тип письма -> DTO контекста» хранится в одном реестре `EMAIL_CONTEXTS` (`src/dto/emails/`): им пользуются шаблонизатор, эндпоинт и предпросмотр. Письма со своей логикой (например, приглашение, которое проверяет статус перед отправкой) оформляются отдельной задачей и сервисной функцией поверх `send`.

Новое письмо: значение в `EmailTemplate` → DTO контекста и запись в `EMAIL_CONTEXTS` → папка шаблона → образец в `SAMPLE_CONTEXTS` (`src/interfaces/cli/email_preview.py`; без записи в реестре или образца падает параметризованный тест на все шаблоны). Если письмо ставится из кода, а не через внутренний эндпоинт: сервисная функция в `application/notifications/` → вызов `enqueue`. Посмотреть результат: `docker compose run --rm app python -m src.interfaces.cli.email_preview` (HTML и текст сохраняются в `.preview/`, открывай в браузере).

## Флоу тестирования эндпоинта

### Запуск

Тесты запускаются в Docker: `docker compose --profile tests run --rm tests` (профиль `tests` указывать обязательно: без него `run` теряет переменные из `env_file`). Зависимости (`db`, `redis`) поднимаются автоматически. Выборочный запуск: `docker compose --profile tests run --rm tests pytest tests/path -k name`.

Тестовая база данных `test_<DB_NAME>` создается тестами (`tests/conftest.py`) на том же сервере PostgreSQL отдельно от основной, миграции накатываются alembic'ом, после прогона база удаляется, поэтому основная БД не затрагивается. Таблицы очищаются перед каждым тестом. Пользователь БД должен иметь право `CREATEDB` (в dev это владелец `DB_USER`).

### Фикстуры

- `container` - инициализирует DI-контейнер и чистит таблицы;
- `uow` - `UnitOfWork` для подготовки и проверки данных в БД (зависит от `container`);
- `api` - `EndpointRegistry` для вызова эндпоинтов (зависит от `container`). Фикстуры `client` нет: HTTP-клиент скрыт внутри реестра.

Каждый тест обязательно использует `uow`, `container` или `api`: они инициализируют DI-контейнер для сервисных функций.

### EndpointRegistry и ResponseWrapper

Эндпоинты в тестах вызываются только через `api`: `await api.auth.login(data)`, `await api.users.me(token)`. Группы эндпоинтов описаны классами в `tests/endpoints/` (наследники `BaseEndpoints`), а в `EndpointRegistry` доступны одноименными свойствами (`auth`, `users`, `internal`). Новый эндпоинт: метод в классе группы; новая группа: класс в `tests/endpoints/` и свойство в `EndpointRegistry`.

Метод эндпоинта принимает DTO (или `dict` для заведомо невалидных payload) и возвращает `ResponseWrapper[SomeDTO]` (`tests/endpoints/response.py`), в который передаются ответ, DTO ответа и успешный статус (по умолчанию 200; для списков - `TypeAdapter(list[SomeDTO])`). Методы обертки:

- `validate()` - проверяет успешный статус и возвращает DTO;
- `expected_error_status(status_code, code=None)` - ожидаемая бизнес-ошибка: проверяет HTTP-статус и (если передан) поле `code` в теле; возвращает сырой `Response`;
- `expect_validation_error(message=None, field=None)` - ожидаемый 422: опционально проверяет подстроку в тексте ошибки и имя поля;
- сырой ответ доступен через `response`, `status_code`, `headers`, `json()` для специфичных проверок (заголовки, отсутствие поля в теле).

Не пиши в тестах ручные `assert response.status_code == ...` и `Model.model_validate_json(response.text)`: для этого есть обертка.

### Структура теста

Для каждого эндпоинта создается отдельный файл с тестами (пример: `tests/interfaces/api/v1/auth/test_register.py`)

```python
from fastapi import status

from tests.factories.users import UserRegisterFactory
from tests.helpers.users import create_users


async def test__success(uow, api):
    data = UserRegisterFactory.build()

    token = (await api.auth.register(data)).validate()

    async with uow.connection():
        user = await uow.users.get_by_email(data.email)
    assert token.token_type == "bearer"
    assert user.fullname == data.fullname


async def test__failed__duplicated_email(uow, api):
    created_user = (await create_users(uow))[0]
    data = UserRegisterFactory.build(email=created_user.email)

    (await api.auth.register(data)).expected_error_status(status.HTTP_409_CONFLICT, "user_email_exists")


async def test__failed__short_password(container, api):
    payload = {"fullname": "Test", "email": "test@example.com", "password": "short"}

    (await api.auth.register(payload)).expect_validation_error("at least 8 characters", field="password")
```

Важно:
- Подготовка данных для создания объектов в БД должна осуществляться через Factory-классы (`tests/factories/`)
- Если в тестах повторяются какие-то операции, их следует вынести во вспомогательные функции (`tests/helpers/`): создание пользователей (`create_users`), выпуск токенов (`make_token`, `encode_raw_token`)
- Конвенция по наименованию тестов: `test__success` - успешный, `test__failed__not_admin` - проваленный тест
- Покрывай успешный сценарий, ошибки валидации (с проверкой поля), границы значений, отсутствие прав (401/403) и отсутствие сущности (404)
- Для эндпоинтов с аутентификацией проверяй: нет заголовка, мусорный токен, просроченный токен, чужую подпись, токен удаленного пользователя
- Сценарии, специфичные для одного теста (параллельные запросы, перехеширование), остаются в самом тесте, а не в обертке
- Для тестов, в которых возвращается список моделей, используй `TypeAdapter(list[EntityDTO])` в качестве типа ответа в `ResponseWrapper`
