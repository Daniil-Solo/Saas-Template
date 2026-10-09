// Мост между API-клиентом и слоем features/auth: shared не знает о features,
// поэтому доступ к токену и реакция на 401 регистрируются снаружи (см. features/auth/setup.ts).

type AuthHandlers = {
  getToken: () => string | null;
  onUnauthorized: () => void;
};

let handlers: AuthHandlers = {
  getToken: () => null,
  onUnauthorized: () => {},
};

export function configureApiAuth(next: AuthHandlers): void {
  handlers = next;
}

export function getApiToken(): string | null {
  return handlers.getToken();
}

export function handleUnauthorized(): void {
  handlers.onUnauthorized();
}
