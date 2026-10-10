import type { QueryClient } from "@tanstack/react-query";

import { configureApiAuth } from "@/shared/api";
import { setSentryUser } from "@/shared/observability/sentry";

import { clearToken, getToken } from "./token-storage";

/** Подключает токен к API-клиенту и сбрасывает сессию при ответе 401. Вызывается один раз при старте. */
export function setupAuth(queryClient: QueryClient): void {
  configureApiAuth({
    getToken,
    onUnauthorized: () => {
      clearToken();
      setSentryUser(null);
      queryClient.clear();
    },
  });
}
