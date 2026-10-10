const STORAGE_KEY = "last_organization_id";

// localStorage может быть недоступен (приватный режим, запрет сайта) - тогда просто ничего не помним
export function getLastOrganizationId(): number | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value !== null && /^\d+$/.test(value) ? Number(value) : null;
  } catch {
    return null;
  }
}

export function setLastOrganizationId(orgId: number): void {
  try {
    localStorage.setItem(STORAGE_KEY, String(orgId));
  } catch {
    // не критично
  }
}

export function clearLastOrganizationId(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // не критично
  }
}
