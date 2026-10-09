# SaaS Template

Шаблон для быстрого старта веб-приложений (в том числе microSaaS): готовые backend и frontend, Docker-окружение для разработки и production-конфигурация.

- **backend/** — FastAPI, PostgreSQL, Redis, S3 (MinIO): аутентификация, пользователи, миграции, email, rate limiting, LLM-инфраструктура.
- **frontend/** — React, Vite, TypeScript, Tailwind + shadcn/ui: роутинг, авторизация, типизированный API-клиент.
- **docs/** — схема развертывания и описания фич.

## Быстрый старт (разработка)

Нужен только Docker. Зависимости на хост ставить не требуется.

```bash
./scripts/run_dev.sh        # поднять backend + frontend (down - остановить, logs - логи)
```

Скрипт создаст `.env` из примеров, общую сеть и запустит оба проекта. В конце он выведет адреса и список того, что нужно определить самостоятельно (ключ email, секреты для production и т.д.).

- Приложение: http://localhost:5173
- API и документация: http://localhost:8000/docs

Подробности: [backend/docs/development.md](backend/docs/development.md), [frontend/docs/development.md](frontend/docs/development.md).

## Production

Разворачивается на одном сервере через Docker Compose с автоматическим HTTPS (Caddy).

```bash
cp .example.env .env    # заполните все значения <...>
docker compose up -d --build
```

Подробности и схема: [docs/deployment.md](docs/deployment.md).

## Документация

- [Развертывание](docs/deployment.md)
- [Архитектура backend](backend/docs/architecture/architecture.md), [модель данных](backend/docs/architecture/data_model.md)
- [Архитектура frontend](frontend/docs/architecture/architecture.md), [маршруты](frontend/docs/architecture/routes.md)
- [Описание фич](docs/usecases/README.md)
