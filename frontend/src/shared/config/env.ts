import { z } from "zod";

const envSchema = z.object({
  // Пусто - запросы идут на тот же origin (/api/...)
  VITE_API_URL: z.string().default(""),
});

const parsed = envSchema.parse(import.meta.env);

export const config = {
  apiUrl: parsed.VITE_API_URL,
} as const;
