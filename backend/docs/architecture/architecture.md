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
        cache("БД типа 'ключ-значение'")
    end
    subgraph External["Внешние системы"]
        llm("LLM API")
        email("Сервис отправки email")
    end

    %% Коммуникации внутри
    frontend --> api

    api --> db
    api --> cache
    api --> storage
    worker --> db
    worker --> storage

    %% Коммуникации с внешними системами
    api --> email
    api --> llm
    worker --> llm

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
    Email["Сервис email <br>[Maileroo]"]:::existing
    User((Пользователь)):::person
    Frontend("Frontend <br>[Container: Nginx + SPA]"):::container
    API("Backend API <br>[Container: FastAPI]"):::container
    Worker("Worker <br>[Container: Python]"):::container
    DB[("Основные данные <br>[Container: PostgreSQL]")]:::database
    S3[("Файлы <br>[Container: MinIO / S3]")]:::database
    KVDB[("Rate limiting, кеш <br>[Container: Redis]")]:::database

    %% connections and boundaries %%
    subgraph Legend [Containers]
        User-.->|Uses| Frontend

        subgraph Boundary["Boundary: System"]
            Frontend-.->|"Makes requests <br> [HTTP/HTTPS]"| API
            API-.->|"Reads/writes <br> [TCP]"| DB
            API-.->|"Reads/writes <br> [TCP]"| KVDB
            API-.->|"Reads/writes <br> [HTTP/HTTPS]"| S3

            Worker-.->|"Reads/writes <br> [TCP]"| DB
            Worker-.->|"Reads/writes <br> [HTTP/HTTPS]"| S3
        end
        class Boundary boundary

        API-.->|"Sends emails <br> [HTTP/HTTPS]"| Email
        API-.->|"Makes requests <br> [HTTP/HTTPS]"| LLM
        Worker-.->|"Makes requests <br> [HTTP/HTTPS]"| LLM
    end
    class Legend frame
```
