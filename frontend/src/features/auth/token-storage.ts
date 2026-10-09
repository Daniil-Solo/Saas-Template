// Единственное место, где хранится access-токен. Остальной код получает его через API-клиент.

const TOKEN_KEY = "access_token";

const listeners = new Set<() => void>();

function notify(): void {
  for (const listener of listeners) {
    listener();
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // хранилище недоступно - сессия не сохранится
  }
  notify();
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // хранилище недоступно - сбрасывать нечего
  }
  notify();
}

/** Подписка для useSyncExternalStore: реагирует на изменения в этой и в других вкладках. */
export function subscribeToken(listener: () => void): () => void {
  listeners.add(listener);
  const onStorage = (event: StorageEvent) => {
    if (event.key === TOKEN_KEY || event.key === null) {
      listener();
    }
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}
