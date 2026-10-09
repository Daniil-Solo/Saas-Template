import { createBrowserRouter, type RouteObject } from "react-router";

import { PublicOnly, RequireAuth } from "@/features/auth";
import { HomePage } from "@/pages/home/home-page";
import { LoginPage } from "@/pages/login/login-page";
import { NotFoundPage } from "@/pages/not-found/not-found-page";
import { RegisterPage } from "@/pages/register/register-page";

// Маршруты и права доступа - по frontend/docs/architecture/routes.md
export const routes: RouteObject[] = [
  {
    element: <PublicOnly />,
    children: [
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
    ],
  },
  {
    element: <RequireAuth />,
    children: [{ path: "/", element: <HomePage /> }],
  },
  { path: "*", element: <NotFoundPage /> },
];

export const router = createBrowserRouter(routes);
