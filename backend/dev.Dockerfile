FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.20 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

# Зависимости ставятся отдельным слоем для кеширования (вместе с dev-группой: ruff, mypy, pytest)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project --frozen

COPY . /app

# В dev-окружении код монтируется томом (.:/app), поэтому команда запуска переопределяется в compose
CMD ["uvicorn", "src.interfaces.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
