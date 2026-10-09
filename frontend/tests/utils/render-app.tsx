import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { createQueryClient, Providers } from "@/app/providers";
import { routes } from "@/app/router";

/** Рендерит приложение целиком (провайдеры + маршруты) начиная с указанного пути. */
export function renderApp(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <Providers queryClient={createQueryClient()}>
      <RouterProvider router={router} />
    </Providers>,
  );
  return router;
}
