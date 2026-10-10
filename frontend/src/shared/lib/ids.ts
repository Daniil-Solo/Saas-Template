/** Числовой идентификатор из параметра маршрута; null, если значение отсутствует или не число. */
export function parseIdParam(value: string | undefined): number | null {
  if (value === undefined || !/^\d+$/.test(value)) {
    return null;
  }
  return Number(value);
}
