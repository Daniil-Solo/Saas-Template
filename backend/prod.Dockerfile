FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.20 /uv /uvx /bin/

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Только production-зависимости (без dev-группы: ruff, mypy, pytest)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project --no-dev --frozen


FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Непривилегированный пользователь без shell и домашней директории
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app . /app

USER app

EXPOSE 8000

# Команда запуска переопределяется в compose для app, worker и migrate
CMD ["uvicorn", "src.interfaces.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
