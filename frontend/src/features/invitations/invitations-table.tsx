import { Button } from "@/shared/ui/button";
import { FormError } from "@/shared/ui/form-error";

import { useInvitations, useRevokeInvitation } from "./api";
import { formatDateTime, STATUS_LABELS } from "./status";

type InvitationsTableProps = {
  orgId: number;
};

export function InvitationsTable({ orgId }: InvitationsTableProps) {
  const invitations = useInvitations(orgId);
  const revoke = useRevokeInvitation(orgId);

  if (invitations.isPending) {
    return <p role="status">Загрузка приглашений...</p>;
  }
  if (invitations.isError) {
    return (
      <div className="flex flex-col items-start gap-3">
        <FormError error={invitations.error} />
        <Button type="button" variant="outline" onClick={() => invitations.refetch()}>
          Повторить
        </Button>
      </div>
    );
  }
  if (invitations.data.length === 0) {
    return <p className="text-sm text-muted-foreground">Приглашений пока нет.</p>;
  }
  return (
    <div className="flex flex-col gap-3">
      {revoke.error ? <FormError error={revoke.error} /> : null}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b text-muted-foreground">
              <th className="py-2 pr-4 font-medium">Email</th>
              <th className="py-2 pr-4 font-medium">Роли</th>
              <th className="py-2 pr-4 font-medium">Статус</th>
              <th className="py-2 pr-4 font-medium">Действует до</th>
              <th className="py-2 font-medium">
                <span className="sr-only">Действия</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {invitations.data.map((invitation) => (
              <tr key={invitation.id} className="border-b">
                <td className="py-2 pr-4">{invitation.email}</td>
                <td className="py-2 pr-4">
                  {invitation.roles.length > 0
                    ? invitation.roles.map((role) => role.name).join(", ")
                    : "—"}
                </td>
                <td className="py-2 pr-4">{STATUS_LABELS[invitation.status]}</td>
                <td className="py-2 pr-4">{formatDateTime(invitation.expires_at)}</td>
                <td className="py-2">
                  {invitation.status === "active" ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={revoke.isPending}
                      aria-label={`Отозвать приглашение для ${invitation.email}`}
                      onClick={() => revoke.mutate(invitation.id)}
                    >
                      Отозвать
                    </Button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
