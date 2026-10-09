import { Navigate, Outlet, useLocation } from "react-router";

import { useIsAuthenticated } from "./api";

/** Приватные маршруты: неавторизованный пользователь уходит на /login. */
export function RequireAuth() {
  const isAuthenticated = useIsAuthenticated();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

/** Публичные маршруты входа и регистрации: авторизованный пользователь уходит на /. */
export function PublicOnly() {
  const isAuthenticated = useIsAuthenticated();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
