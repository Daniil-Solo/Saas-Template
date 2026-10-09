## Модель развертывания

Схемы - источник истины по тому, как система разворачивается. При изменении состава сервисов сначала обновляются схемы, затем `dev.docker-compose.yml` и production-конфигурация.

### Локальная разработка

Описана в `dev.docker-compose.yml`. Frontend запускается отдельным compose-проектом и общается с backend через внешнюю docker-сеть `dev-network`.

```mermaid
flowchart LR
    browser("Браузер")

    subgraph Frontend["Compose-проект frontend"]
        web("web")
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

    browser --> web
    browser --> app
    web --> shared
    shared --> app

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

В `dev-network` подключен только `app` (алиас `backend`). БД, S3 и Redis недоступны из других проектов и опубликованы на хосте только на `127.0.0.1`.

### Production (ориентир)

Для production в шаблоне пока нет готовых файлов. Рекомендуемая схема для одного сервера в Docker:

```mermaid
flowchart TD
    user("Пользователь") -->|":80/:443"| caddy("reverse proxy: Caddy")

    caddy --> web("web: Nginx + SPA")
    web --> api("api: FastAPI")

    api --> db[("db: PostgreSQL")]
    api --> redis[("cache: Redis")]
    api --> s3[("storage: MinIO / S3")]

    worker("worker: Python") --> db
    worker --> s3
```

При развертывании:
- наружу публикуется только reverse proxy, остальные сервисы доступны во внутренней docker-сети;
- секреты (`AUTH_SECRET_KEY`, `SECURITY_ENCRYPTION_KEY`, пароли БД/Redis/S3) заменяются на уникальные значения, значения из `.example.env` использовать нельзя;
- данные PostgreSQL, MinIO и Redis хранятся в docker-томах с регулярным резервным копированием;
- при необходимости мониторинга добавляются Prometheus, Loki и Grafana, но шаблон их не включает.
