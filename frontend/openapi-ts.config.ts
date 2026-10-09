import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: process.env.OPENAPI_URL ?? "http://backend:8000/openapi.json",
  output: "src/shared/api/generated",
  plugins: [
    "@hey-api/typescript",
    "@hey-api/sdk",
    // baseUrl и токен подставляются в рантайме, см. src/shared/api/client-config.ts
    { name: "@hey-api/client-fetch", runtimeConfigPath: "@/shared/api/client-config" },
  ],
});
