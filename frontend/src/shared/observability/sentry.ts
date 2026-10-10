import * as Sentry from "@sentry/react";

import { ApiError } from "@/shared/api";
import { config } from "@/shared/config/env";

/** Ожидаемые ошибки API (4xx) в Sentry не отправляем. */
export function beforeSend<T extends Sentry.ErrorEvent>(
  event: T,
  hint: Sentry.EventHint,
): T | null {
  const error = hint.originalException;
  if (error instanceof ApiError && error.status !== null && error.status < 500) {
    return null;
  }
  return event;
}

/** Без `VITE_SENTRY_DSN` Sentry выключен и SDK не инициализируется. */
export function initSentry(): void {
  if (!config.sentryDsn) {
    return;
  }
  Sentry.init({
    dsn: config.sentryDsn,
    environment: config.sentryEnvironment,
    release: config.appRelease,
    // В v11 вместо sendDefaultPii: ничего персонального не собираем автоматически (user.id ставим вручную)
    dataCollection: { userInfo: false, cookies: false, httpBodies: [], urlQueryParams: false },
    tracesSampleRate: 0,
    beforeSend,
  });
}

/** В Sentry уходит только id пользователя; `null` сбрасывает пользователя (выход, 401). */
export function setSentryUser(id: number | null): void {
  Sentry.setUser(id === null ? null : { id: String(id) });
}

export { ErrorBoundary } from "@sentry/react";
