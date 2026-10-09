## Модель развертывания

Схемы - источник истины по тому, как система разворачивается. При изменении состава сервисов сначала обновляются схемы, затем `dev.docker-compose.yml` соответствующего проекта (`backend/`, `frontend/`) и production-конфигурация.

### Локальная разработка

Каждый проект описан в своем `dev.docker-compose.yml` и запускается отдельным compose-проектом. Проекты общаются через внешнюю docker-сеть `dev-network`.

```mermaid
flowchart LR
    browser("Браузер")

    subgraph Frontend["Compose-проект frontend"]
        web("web: Vite dev server :5173")
        ftests("tests: vitest<br>(profile tests)")
        e2e("e2e: Playwright<br>(profile e2e)")
    end

    subgraph Backend["Compose-проект backend"]
        app("app: FastAPI :8000")
        worker("worker: Python<br>(profile worker)")
        tests("tests: pytest<br>(profile tests)")
        db[("db: PostgreSQL")]
        s3[("s3: MinIO")]
        redis[("redis: Redis")]
    end

    shared{{"Docker network: dev-network"}}

    browser -->|":5173"| web
    browser -->|":8000 (docs)"| app
    web -->|"proxy /api"| shared
    shared -->|"http://backend:8000"| app
    e2e --> web

    app --> db
    app --> s3
    app --> redis
    worker --> db
    worker --> s3
    worker --> redis
    tests --> db
    tests --> s3
    tests --> redis
```

- Браузер ходит только на Vite (`:5173`); запросы `/api/*` Vite проксирует на backend, поэтому CORS в dev не нужен.
- В `dev-network` подключен только `app` (алиас `backend`). БД, S3 и Redis недоступны из других проектов и опубликованы на хосте только на `127.0.0.1`.

### Production

Production разворачивается на одном сервере через Docker из корня репозитория. Файлы: `prod.docker-compose.yml`, `Caddyfile`, `.example.env` (шаблон `.env`), `backend/prod.Dockerfile`, `frontend/prod.Dockerfile`, `frontend/nginx.conf`.

```mermaid
flowchart TD
    user("Пользователь") -->|":80/:443"| caddy("caddy: reverse proxy + HTTPS")

    subgraph edge["Сеть edge"]
        caddy
        web("web: Nginx + SPA (dist) :8080")
        api("api: FastAPI :8000")
        worker("worker: Python")
    end

    subgraph data["Сеть data (internal, без выхода в интернет)"]
        migrate("migrate: alembic upgrade head<br>(одноразовая задача)")
        db[("db: PostgreSQL")]
        redis[("redis: Redis")]
        s3[("s3: MinIO")]
    end

    caddy -->|"/"| web
    caddy -->|"/api (кроме /api/internal)"| api

    migrate --> db
    api --> db
    api --> redis
    api --> s3
    worker --> db
    worker --> redis
    worker --> s3
```

Запуск:

```bash
cp .example.env .env              # заполнить все значения <...> уникальными секретами
docker compose up -d --build
```

Безопасность:
- на хосте опубликованы только порты 80 и 443 сервиса `caddy`; БД, Redis и MinIO (в том числе консоль) снаружи недоступны, их сеть `data` помечена `internal` и не имеет выхода в интернет;
- `api` и `worker` подключены к обеим сетям (им нужен доступ к данным и во внешние API), `web` и `caddy` - только к `edge`;
- Caddy автоматически выпускает HTTPS-сертификаты для `DOMAIN`, добавляет security-заголовки и скрывает `/api/internal/*` (healthcheck);
- контейнеры работают без root (кроме штатных образов БД), с `no-new-privileges`, отброшенными capabilities и read-only файловой системой у приложений;
- обязательные секреты заданы без значений по умолчанию (`${VAR:?}`): без заполненного `.env` compose не стартует; `.env` в git не попадает, значения из `.example.env` использовать нельзя;
- API и SPA живут на одном origin, поэтому `VITE_API_URL` остается пустым; в бандл не попадают секреты: всё из `VITE_*` публично;
- миграции применяет сервис `migrate` перед запуском `api` и `worker`;
- данные PostgreSQL, MinIO и Redis хранятся в docker-томах, резервное копирование настраивается отдельно;
- статика SPA кешируется по хешу в имени файла (`/assets/`), `index.html` - без кеша;
- при необходимости мониторинга добавляются Prometheus, Loki и Grafana, но шаблон их не включает.
