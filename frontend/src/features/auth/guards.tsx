import { Navigate, Outlet, useLocation } from "react-router";

import { useIsAuthenticated } from "./api";
import { buildAuthPath, useNextPath } from "./next-path";

/** Приватные маршруты: неавторизованный пользователь уходит на /login и после входа возвращается на исходный путь. */
export function RequireAuth() {
  const isAuthenticated = useIsAuthenticated();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to={buildAuthPath("/login", location.pathname + location.search)} replace />;
  }
  return <Outlet />;
}

/** Публичные маршруты входа и регистрации: авторизованный пользователь уходит на `next` или на /. */
export function PublicOnly() {
  const isAuthenticated = useIsAuthenticated();
  const next = useNextPath();

  if (isAuthenticated) {
    return <Navigate to={next ?? "/"} replace />;
  }
  return <Outlet />;
}
