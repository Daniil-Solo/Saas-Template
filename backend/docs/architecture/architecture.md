## Архитектура шаблона

Диаграммы - источник истины по составу системы и отправная точка разработки. Новый контейнер, воркер или внешняя интеграция сначала добавляется на диаграммы, и только потом реализуется в коде и в `dev.docker-compose.yml`.

Сейчас показаны компоненты шаблона «из коробки».

### Без технологий

```mermaid
flowchart LR
    user("Пользователь")

    subgraph System["Система"]
        frontend("Веб-клиент")
        api("API-сервер")
        worker("Воркер")
        db("Реляционная БД")
        storage("Файловое хранилище")
        cache("БД типа 'ключ-значение':<br>очередь задач, rate limiting")
        metrics("Сбор метрик и графики")
    end
    subgraph External["Внешние системы"]
        llm("LLM API")
        email("Сервис отправки email")
        errors("Сервис отслеживания ошибок")
    end

    %% Коммуникации внутри
    frontend --> api
    metrics --> api

    api --> db
    api --> cache
    api --> storage
    worker --> db
    worker --> storage
    worker --> cache

    %% Коммуникации с внешними системами
    worker --> email
    api --> llm
    worker --> llm
    api --> errors
    frontend --> errors

    %% Внешний доступ пользователя
    user --> frontend
```

### C4 - уровень контейнеров

```mermaid
graph LR
    %% C4 style classes c4model.com %%
    classDef person fill:#08427b,stroke:black,color:white;
    classDef container fill:#1168bd,stroke:black,color:white;
    classDef database fill:#1168bd,stroke:black,color:white;
    classDef existing fill:#999999,stroke:black,color:white;
    classDef boundary fill:white,stroke:black,stroke-width:2px,stroke-dasharray: 5 5;
    classDef frame fill:white,stroke:black;

    %% nodes %%
    LLM["LLM API"]:::existing
    Email["Сервис email <br>[SMTP-сервер или Maileroo]"]:::existing
    User((Пользователь)):::person
    Frontend("Frontend <br>[Container: Nginx + SPA]"):::container
    API("Backend API <br>[Container: FastAPI]"):::container
    Worker("Worker <br>[Container: Python, arq]"):::container
    DB[("Основные данные <br>[Container: PostgreSQL]")]:::database
    S3[("Файлы <br>[Container: MinIO / S3]")]:::database
    KVDB[("Очередь задач, rate limiting, кеш <br>[Container: Redis]")]:::database
    Prom("Метрики <br>[Container: Prometheus]"):::container
    Grafana("Графики <br>[Container: Grafana]"):::container
    Sentry["Отслеживание ошибок <br>[Sentry]"]:::existing

    %% connections and boundaries %%
    subgraph Legend [Containers]
        User-.->|Uses| Frontend

        subgraph Boundary["Boundary: System"]
            Frontend-.->|"Makes requests <br> [HTTP/HTTPS]"| API
            API-.->|"Reads/writes <br> [TCP]"| DB
            API-.->|"Reads/writes, ставит задачи <br> [TCP]"| KVDB
            API-.->|"Reads/writes <br> [HTTP/HTTPS]"| S3

            Worker-.->|"Берёт задачи <br> [TCP]"| KVDB
            Worker-.->|"Reads/writes <br> [TCP]"| DB
            Worker-.->|"Reads/writes <br> [HTTP/HTTPS]"| S3

            Prom-.->|"Scrapes /api/internal/metrics <br> [HTTP]"| API
            Grafana-.->|"Queries <br> [HTTP]"| Prom
        end
        class Boundary boundary

        Worker-.->|"Sends emails <br> [SMTP / HTTPS]"| Email
        API-.->|"Makes requests <br> [HTTP/HTTPS]"| LLM
        Worker-.->|"Makes requests <br> [HTTP/HTTPS]"| LLM
        API-.->|"Sends errors, optional <br> [HTTPS]"| Sentry
        Frontend-.->|"Sends errors, optional <br> [HTTPS]"| Sentry
    end
    class Legend frame
```

### Backend: компоненты наблюдаемости и настройки

Слои — по `backend/AGENTS.md`; `infrastructure` не импортирует `application`.

```mermaid
flowchart TD
    subgraph App["create_app"]
        settings("settings: Settings<br>app, db, redis, auth, invitations, admin,<br>email (smtp, maileroo), logging, metrics, sentry")
        mw("interfaces/api/middleware:<br>request_id, лог http_request, метрики")
        metricsEp("GET /api/internal/metrics<br>(вне OpenAPI)")
        deps("dependencies.get_current_user:<br>user_id в контекст логов и Sentry")
    end

    subgraph Obs["infrastructure/observability"]
        logging("logging: structlog,<br>console | json")
        metrics("metrics: prometheus-client")
        sentry("sentry: sentry-sdk,<br>только при заданном SENTRY_DSN")
    end

    container("DI Container: settings,<br>производные auth/db/invitations/admin")
    prom("Prometheus")
    sentryExt("Sentry (внешний)")

    settings --> logging
    settings --> sentry
    settings --> metrics
    settings --> container
    mw --> logging
    mw --> metrics
    deps --> logging
    deps --> sentry
    metricsEp --> metrics
    prom -->|"scrape"| metricsEp
    sentry -.->|"непредвиденные ошибки,<br>без ApplicationError"| sentryExt
```

### Backend: фоновые задачи и письма

Слои — по `backend/AGENTS.md`. `application` не знает про arq и конкретные коннекторы: только интерфейсы `TaskQueue`, `EmailSender`, `EmailTemplater`.

```mermaid
flowchart TD
    admin("Администратор<br>(браузер / скрипт)")
    user("Пользователь")

    subgraph Interfaces["interfaces"]
        auth("api/v1/auth:<br>POST register")
        inv("api/v1/invitations:<br>создание приглашения")
        notif("api/v1/notifications:<br>POST email, GET templates<br>(только админ)")
        tasks("tasks/emails.py:<br>тонкие задачи arq,<br>ретраи")
        preview("cli/email_preview:<br>предпросмотр писем")
    end

    subgraph App["application"]
        reg("auth.register")
        invc("invitations.create")
        svc("notifications/emails:<br>enqueue_email, send,<br>send_invitation")
    end

    subgraph Infra["infrastructure"]
        queue("queue: TaskQueue<br>(ArqTaskQueue)")
        templater("email_templater: EmailTemplater<br>(Jinja2, шаблоны, EMAIL_CONTEXTS)")
        sender("email_sender: EmailSender<br>console | smtp | maileroo<br>(EMAIL_BACKEND)")
    end

    redis[("Redis")]
    ext("SMTP-сервер /<br>Maileroo API")

    user --> auth
    user --> inv
    admin --> notif
    auth --> reg
    inv --> invc
    notif --> svc
    reg -->|"enqueue после коммита"| queue
    invc -->|"enqueue после коммита"| queue
    svc -->|"enqueue SEND_EMAIL"| queue
    queue --> redis
    redis -->|"воркер берёт задачу"| tasks
    tasks --> svc
    svc --> templater
    svc --> sender
    preview --> templater
    sender --> ext
```

- Письма уходят только из воркера; API лишь ставит задачу в очередь.
- `EMAIL_BACKEND=console` (по умолчанию) пишет письмо в лог; при старте API и воркера выводится предупреждение.
- Добавить коннектор — новый класс `EmailSender`, группа настроек и строка в селекторе DI; добавить письмо — значение `EmailTemplate`, DTO контекста в `EMAIL_CONTEXTS`, папка шаблона.
