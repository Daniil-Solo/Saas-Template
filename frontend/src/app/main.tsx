import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";

import "@/shared/api"; // подключает перехватчики API-клиента
import { initSentry } from "@/shared/observability/sentry";
import { createQueryClient, Providers } from "./providers";
import { router } from "./router";
import "./styles.css";

initSentry();

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Не найден элемент #root");
}

createRoot(rootElement).render(
  <StrictMode>
    <Providers queryClient={createQueryClient()}>
      <RouterProvider router={router} />
    </Providers>
  </StrictMode>,
);
