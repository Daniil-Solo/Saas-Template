FROM node:22-slim

ENV PNPM_HOME=/pnpm \
    PATH="/pnpm:$PATH" \
    CI=true

RUN corepack enable

WORKDIR /app

# Зависимости ставятся отдельным слоем для кеширования (вместе с dev-зависимостями: biome, vitest, playwright)
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . /app

# В dev-окружении код монтируется томом (.:/app), поэтому команда запуска переопределяется в compose
CMD ["pnpm", "dev", "--host", "0.0.0.0"]
