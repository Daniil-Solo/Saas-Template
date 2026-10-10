import { useSearchParams } from "react-router";

/** Допустим только путь внутри приложения: иначе `?next=` стал бы открытым редиректом. */
export function sanitizeNext(value: string | null): string | null {
  if (value === null || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) {
    return null;
  }
  return value;
}

/** Путь страницы входа с возвратом на `next` (для главной возврат не нужен). */
export function buildAuthPath(base: "/login" | "/register", next: string | null): string {
  if (next === null || next === "/") {
    return base;
  }
  return `${base}?next=${encodeURIComponent(next)}`;
}

/** Безопасный `next` из адресной строки или null. */
export function useNextPath(): string | null {
  const [searchParams] = useSearchParams();
  return sanitizeNext(searchParams.get("next"));
}
