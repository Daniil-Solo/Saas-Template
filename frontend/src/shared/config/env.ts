import { z } from "zod";

const envSchema = z.object({
  // Пусто - запросы идут на тот же origin (/api/...)
  VITE_API_URL: z.string().default(""),
  // Пустой DSN - Sentry выключен. DSN публичен по природе, как и все VITE_*
  VITE_SENTRY_DSN: z.string().default(""),
  VITE_SENTRY_ENVIRONMENT: z.string().default(""),
  VITE_APP_RELEASE: z.string().default(""),
});

const parsed = envSchema.parse(import.meta.env);

export const config = {
  apiUrl: parsed.VITE_API_URL,
  sentryDsn: parsed.VITE_SENTRY_DSN || null,
  sentryEnvironment: parsed.VITE_SENTRY_ENVIRONMENT || undefined,
  appRelease: parsed.VITE_APP_RELEASE || undefined,
} as const;
