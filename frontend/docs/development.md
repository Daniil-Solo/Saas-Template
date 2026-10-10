## Гайд для разработчика

Вся разработка идет через Docker: Node.js и зависимости на хост ставить не нужно. Все команды проекта (pnpm, biome, tsc, vitest, playwright) выполняются внутри контейнеров.

### Dev-окружение

Файлы окружения: `dev.docker-compose.yml`, `dev.Dockerfile`, `.example.env`. Сервисы:

- `web` - Vite dev server, порт 5173, hot reload, код монтируется томом;
- `tests` - vitest (профиль `tests`);
- `e2e` - Playwright (профиль `e2e`).

Файл `dev.docker-compose.yml` подключается через переменную `COMPOSE_FILE` из `.env`, поэтому команды выполняются из папки `frontend/` как обычный `docker compose ...`. Если контейнер `web` не запущен, вместо `exec` используйте `run --rm web ...`.

Сеть: Vite проксирует `/api` на `http://backend:8000` (алиас backend-проекта в `dev-network`), поэтому backend должен быть запущен. Из браузера backend доступен на `localhost:8000`, но клиент должен ходить через прокси, а не напрямую. Общая схема - `../docs/deployment.md`.

### Первый запуск

```bash
cp .example.env .env                  # значения из примера рабочие для dev
docker network create dev-network     # один раз; общая сеть с backend (если уже создана - пропустить)
docker compose up -d --build web      # поднимает Vite dev server
```

Backend запускается отдельно (`backend/`, см. его `docs/development.md`).

После запуска:
- приложение: http://localhost:5173
- API backend (документация): http://localhost:8000/docs

Логи: `docker compose logs --tail=100 web`.

Остановка: `docker compose down`. Удаление томов (`down -v`) делайте только осознанно.

### Переменные окружения

Новая переменная добавляется в `src/shared/config/` и в `.example.env`, затем (если нужно) в локальный `.env`. Всё с префиксом `VITE_` попадает в бандл и публично, секреты там хранить нельзя.

#### Sentry

Отправка ошибок браузера в Sentry настраивается переменными (все публичны, попадают в бандл):

- `VITE_SENTRY_DSN` - DSN проекта Sentry; пусто (по умолчанию) - Sentry выключен и SDK не инициализируется;
- `VITE_SENTRY_ENVIRONMENT` - имя окружения (`production`, `staging`);
- `VITE_APP_RELEASE` - версия релиза.

В prod переменные передаются как build-аргументы (`prod.Dockerfile`, `build.args` в `prod.docker-compose.yml`), поэтому менять их нужно пересборкой образа `web`. В Sentry уходит только `user.id`; ошибки API 4xx не отправляются; трейсинг и replay выключены. Инициализация - `src/shared/observability/sentry.ts`.

### Установка зависимостей

Менеджер пакетов - pnpm. Зависимости ставятся при сборке образа из `package.json` и `pnpm-lock.yaml`. Чтобы добавить библиотеку:

```bash
docker compose run --rm web pnpm add <пакет>            # добавить зависимость
docker compose run --rm web pnpm add -D <пакет>         # добавить dev-зависимость
docker compose up -d --build web                        # пересобрать образ
```

TypeScript закреплён на `~6.0`: `@hey-api/openapi-ts` пока не работает с нативным TypeScript 7 (нет JS API), поэтому при `pnpm add` не поднимайте major-версию.

UI-компоненты shadcn добавляются командой `docker compose run --rm web pnpm dlx shadcn@latest add <компонент>`.

### Линтер, форматирование, типы

```bash
docker compose exec web pnpm format        # biome format --write
docker compose exec web pnpm lint          # biome check --write (линтер + импорты)
docker compose exec web pnpm typecheck     # tsc --noEmit
```

### API-клиент

Типы и функции запросов генерируются из OpenAPI-схемы backend (`OPENAPI_URL`) и кладутся в `src/shared/api/generated/`. Руками этот каталог не правится.

```bash
docker compose exec web pnpm gen:api       # перегенерировать клиент (backend должен быть запущен)
```

### Тесты

```bash
docker compose run --rm tests                            # все unit- и компонентные тесты (vitest)
docker compose run --rm tests pnpm test src/path -t name # выборочный запуск
docker compose run --rm e2e                              # E2E (Playwright), нужны запущенные backend и web
```

### Создание нового проекта из шаблона

1. Скопируйте репозиторий и переименуйте проект: `name` в `package.json` и `dev.docker-compose.yml`.
2. Опишите продукт в `AGENTS.md` (раздел «О проекте») и добавьте описания фич в `../docs/usecases/`.
3. Удалите неиспользуемые части (страницы, фичи, зависимости).
4. Начинайте разработку с диаграмм: сначала обновите `docs/architecture/` и `../docs/deployment.md` (страницы и маршруты, компоненты, развертывание), затем реализуйте по ним код по флоу из `AGENTS.md`.
