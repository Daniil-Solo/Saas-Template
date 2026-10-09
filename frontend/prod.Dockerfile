FROM node:22-slim AS builder

ENV PNPM_HOME=/pnpm \
    PATH="/pnpm:$PATH" \
    CI=true

RUN corepack enable

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . /app

# Всё из VITE_* попадает в публичный бандл: секреты сюда передавать нельзя.
# Пустое значение - API на том же origin (/api/...)
ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL

RUN pnpm build


FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

# Слушает 8080 от имени непривилегированного пользователя
EXPOSE 8080
