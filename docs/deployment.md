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

### Production (ориентир)

Для production в шаблоне пока нет готовых файлов. Рекомендуемая схема для одного сервера в Docker:

```mermaid
flowchart TD
    user("Пользователь") -->|":80/:443"| caddy("reverse proxy: Caddy")

    caddy -->|"/"| web("web: Nginx + SPA (dist)")
    caddy -->|"/api"| api("api: FastAPI")

    api --> db[("db: PostgreSQL")]
    api --> redis[("cache: Redis")]
    api --> s3[("storage: MinIO / S3")]

    worker("worker: Python") --> db
    worker --> s3
```

При развертывании:
- наружу публикуется только reverse proxy, остальные сервисы доступны во внутренней docker-сети;
- API и SPA живут на одном origin, поэтому `VITE_API_URL` остается пустым; в бандл не попадают секреты: всё из `VITE_*` публично;
- секреты backend (`AUTH_SECRET_KEY`, `SECURITY_ENCRYPTION_KEY`, пароли БД/Redis/S3) заменяются на уникальные значения, значения из `.example.env` использовать нельзя;
- данные PostgreSQL, MinIO и Redis хранятся в docker-томах с регулярным резервным копированием;
- статика SPA кешируется по хешу в имени файла, `index.html` - без кеша;
- при необходимости мониторинга добавляются Prometheus, Loki и Grafana, но шаблон их не включает.
