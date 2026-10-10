import type { InvitationDisplayStatus } from "@/shared/api/generated";

export const STATUS_LABELS: Record<InvitationDisplayStatus, string> = {
  active: "Действует",
  accepted: "Принято",
  revoked: "Отозвано",
  expired: "Истекло",
};

const dateFormat = new Intl.DateTimeFormat("ru-RU", { dateStyle: "short", timeStyle: "short" });

export function formatDateTime(value: string): string {
  return dateFormat.format(new Date(value));
}
