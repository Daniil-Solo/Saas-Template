import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSyncExternalStore } from "react";

import type { UserLoginDto, UserRegisterDto } from "@/shared/api/generated";
import {
  getMeEndpointApiV1UsersMeGet,
  loginEndpointApiV1AuthLoginPost,
  registerEndpointApiV1AuthRegisterPost,
} from "@/shared/api/generated";

import { clearToken, getToken, setToken, subscribeToken } from "./token-storage";

export const currentUserKey = ["users", "me"] as const;

/** Реактивный токен: компонент перерисовывается при входе и выходе. */
export function useAccessToken(): string | null {
  return useSyncExternalStore(subscribeToken, getToken);
}

export function useIsAuthenticated(): boolean {
  return useAccessToken() !== null;
}

export function useCurrentUser() {
  const token = useAccessToken();
  return useQuery({
    queryKey: currentUserKey,
    queryFn: async () => (await getMeEndpointApiV1UsersMeGet({ throwOnError: true })).data,
    enabled: token !== null,
  });
}

export function useLogin() {
  return useMutation({
    mutationFn: async (body: UserLoginDto) =>
      (await loginEndpointApiV1AuthLoginPost({ body, throwOnError: true })).data,
    onSuccess: (data) => setToken(data.access_token),
  });
}

// По диаграмме routes.md после регистрации пользователь попадает на /login,
// поэтому выданный backend токен не сохраняется.
export function useRegister() {
  return useMutation({
    mutationFn: async (body: UserRegisterDto) =>
      (await registerEndpointApiV1AuthRegisterPost({ body, throwOnError: true })).data,
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return () => {
    clearToken();
    queryClient.clear();
  };
}
