import path from "node:path";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: { "@": path.resolve(import.meta.dirname, "src") },
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      // E2E-контейнер ходит на dev-сервер по имени сервиса web
      allowedHosts: ["web"],
      proxy: {
        "/api": {
          target: env.DEV_PROXY_TARGET || "http://backend:8000",
          changeOrigin: true,
        },
      },
    },
    test: {
      environment: "jsdom",
      globals: true,
      // В Node fetch не принимает относительные URL, поэтому в тестах API на абсолютном адресе (его перехватывает msw)
      env: { VITE_API_URL: "http://localhost" },
      setupFiles: ["./tests/setup.ts"],
      include: ["tests/**/*.test.{ts,tsx}"],
      exclude: ["tests/e2e/**", "node_modules/**"],
    },
  };
});
