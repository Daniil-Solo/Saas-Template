import { config } from "@/shared/config/env";

import { getApiToken } from "./auth-handlers";
import type { CreateClientConfig } from "./generated/client.gen";

// Подключается генератором (runtimeConfigPath в openapi-ts.config.ts) при создании клиента
export const createClientConfig: CreateClientConfig = (override) => ({
  ...override,
  baseUrl: config.apiUrl,
  auth: () => getApiToken() ?? undefined,
});
