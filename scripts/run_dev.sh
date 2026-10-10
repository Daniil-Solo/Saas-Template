#!/usr/bin/env bash
# SaaS Template: запуск всего dev-стенда (backend + frontend) с параметрами по умолчанию.
# Использование: ./scripts/run_dev.sh [up|down|logs]   (по умолчанию up)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cmd="${1:-up}"

command -v docker >/dev/null || { echo "Docker не найден. Установите Docker и повторите." >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "Docker не запущен. Запустите Docker Desktop и повторите." >&2; exit 1; }

case "$cmd" in
  down)
    (cd "$ROOT/frontend" && docker compose down)
    (cd "$ROOT/backend" && docker compose down)
    exit 0
    ;;
  logs)
    (cd "$ROOT/backend" && docker compose logs --tail=100 app worker) || true
    (cd "$ROOT/frontend" && docker compose logs --tail=100 web) || true
    exit 0
    ;;
  up) ;;
  *) echo "Неизвестная команда: $cmd (up|down|logs)" >&2; exit 1 ;;
esac

# .env из примеров (существующие не трогаем)
for dir in backend frontend; do
  if [ ! -f "$ROOT/$dir/.env" ]; then
    cp "$ROOT/$dir/.example.env" "$ROOT/$dir/.env"
    echo "Создан $dir/.env из .example.env"
  fi
done

# Общая сеть между backend и frontend
docker network inspect dev-network >/dev/null 2>&1 || docker network create dev-network >/dev/null

(cd "$ROOT/backend" && docker compose up -d --build app worker prometheus grafana)
(cd "$ROOT/frontend" && docker compose up -d --build web)

cat <<MSG

=== SaaS Template: dev-стенд запущен ===
  Приложение:       http://localhost:5173
  API (Swagger):    http://localhost:8000/docs
  Консоль MinIO:    http://localhost:9001  (minioadmin / minioadmin)
  Grafana:          http://localhost:3000  (admin / admin, дашборд "HTTP")
  Prometheus:       http://localhost:9090

Остановить: ./scripts/run_dev.sh down    Логи: ./scripts/run_dev.sh logs

--- Что нужно определить самим ---
 Сейчас (для работы функций, требующих внешних сервисов):
  * Письма: по умолчанию EMAIL_BACKEND=console - письма пишутся в лог воркера (cd backend && docker compose logs worker),
    наружу не уходят. Для реальной отправки: backend/.env - EMAIL_BACKEND=smtp|maileroo и EMAIL_SMTP_* / EMAIL_MAILEROO_API_KEY
  * backend/.env: EMAIL_FROM и EMAIL_FROM_DISPLAY_NAME - адрес и имя отправителя
  * Проверка SMTP локально: cd backend && docker compose --profile mail up -d mailpit (UI http://localhost:8025)
  * S3-бакет (S3_BUCKET=app): создайте в консоли MinIO, если приложение не создает его само
 Позже (перед выкладкой в production):
  * В корневом .env (из .example.env) заменить все значения <...>
  * AUTH_SECRET_KEY, SECURITY_ENCRYPTION_KEY, DB_PASSWORD, S3_SECRET_KEY, REDIS_PASSWORD - уникальные секреты
  * DOMAIN - домен с DNS-записью на сервер (для HTTPS)
  * Описание продукта в docs/usecases/ и название/брендинг приложения
  * EMAIL_BACKEND=smtp|maileroo и APP_BASE_URL=https://<DOMAIN> (в prod compose APP_BASE_URL задаётся из DOMAIN)
MSG
