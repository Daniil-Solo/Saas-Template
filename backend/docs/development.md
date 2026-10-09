## Гайд для разработчика

Вся разработка идет через Docker: зависимости на хост ставить не нужно. Все команды проекта (ruff, mypy, alembic, pytest, скрипты) выполняются внутри контейнеров.

### Dev-окружение

Файлы окружения: `dev.docker-compose.yml`, `dev.Dockerfile`, `.example.env`. Сервисы:

- `app` - FastAPI, порт 8000, hot reload, код монтируется томом;
- `worker` - фоновый воркер (профиль `worker`);
- `tests` - тесты (профиль `tests`);
- `db` - PostgreSQL, `s3` - MinIO, `redis` - Redis.

Файл `dev.docker-compose.yml` подключается через переменную `COMPOSE_FILE` из `.env`, поэтому команды выполняются из папки `backend/` как обычный `docker compose ...`. Если контейнер `app` не запущен, вместо `exec` используйте `run --rm app ...`.

Сеть: внутри проекта сервисы видят друг друга по именам (`db`, `redis`, `s3`). Контейнеры из других проектов (frontend) подключаются к внешней сети `dev-network` и обращаются к API по адресу `http://backend:8000`. В эту сеть вынесен только `app`, а БД, Redis и S3 снаружи недоступны (на хосте они опубликованы только на 127.0.0.1). Общая схема - `../docs/deployment.md`.

### Первый запуск

```bash
cp .example.env .env                  # значения из примера рабочие для dev
docker network create dev-network     # один раз; общая сеть с другими проектами (например, frontend)
docker compose up -d --build app      # поднимает app вместе с db, s3, redis
```

После запуска:
- API: http://localhost:8000 (документация: http://localhost:8000/docs)
- консоль MinIO: http://localhost:9001 (логин и пароль - `S3_ACCESS_KEY` и `S3_SECRET_KEY` из `.env`). Бакет `S3_BUCKET` нужно создать в консоли, если приложение не создает его само

Логи: `docker compose logs --tail=100 app`.

Остановка: `docker compose down` (данные сохраняются в томах). Полная очистка данных: `docker compose down -v` (удаляет данные разработки, делайте это только осознанно).

### Переменные окружения

Новая переменная добавляется в `src/settings/` и в `.example.env`, затем (если нужно) в локальный `.env`. Секреты в коде и репозитории не хранятся.

### Установка зависимостей

Зависимости ставятся при сборке образа из `pyproject.toml` и `uv.lock`. Чтобы добавить библиотеку:

```bash
docker compose run --rm app uv add <пакет>              # добавить зависимость
docker compose run --rm app uv add --dev <пакет>        # добавить dev-зависимость
docker compose up -d --build app                        # пересобрать образ
```

### Линтеры

```bash
docker compose exec app ruff format src tests
docker compose exec app ruff check --fix src tests
docker compose exec app mypy src
```

### Миграции

```bash
docker compose exec app alembic revision --autogenerate -m "users"   # сгенерировать миграцию
docker compose exec app alembic upgrade head                         # применить миграции
docker compose exec app alembic downgrade -1                         # откатить последнюю
```

### Тесты

```bash
docker compose run --rm tests                            # все тесты
docker compose run --rm tests pytest tests/path -k name  # выборочный запуск
```

Тестовая база создается автоматически на сервере `db`, основная БД не затрагивается.

### Создание нового проекта из шаблона

1. Скопируйте репозиторий и переименуйте проект: `name` в `pyproject.toml` и `dev.docker-compose.yml`, `APP` в `.env`.
2. Опишите продукт в `AGENTS.md` (раздел «О проекте») и добавьте описания фич в `../docs/usecases/`.
3. Удалите неиспользуемые модули инфраструктуры (например, `ai/`, `email_*`, `storage/`) вместе с зависимостями, настройками и переменными окружения.
4. Замените секреты из `.example.env` на собственные значения для любых окружений, кроме локальной разработки.
5. Начинайте разработку с диаграмм: сначала обновите `docs/architecture/` и `../docs/deployment.md` (компоненты, модель данных, развертывание), затем реализуйте по ним код по флоу из `AGENTS.md`.
