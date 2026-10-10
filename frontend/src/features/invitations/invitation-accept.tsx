import type { OrganizationDto } from "@/shared/api/generated";
import { Button } from "@/shared/ui/button";
import { FormError } from "@/shared/ui/form-error";

import { useAcceptInvitation, useInvitationPreview } from "./api";
import { formatDateTime } from "./status";

type InvitationAcceptProps = {
  token: string;
  onAccepted: (organization: OrganizationDto) => void;
};

const INACTIVE_MESSAGES = {
  accepted: "Это приглашение уже принято.",
  revoked: "Это приглашение отозвано.",
  expired: "Срок действия приглашения истёк. Попросите прислать новое.",
} as const;

export function InvitationAccept({ token, onAccepted }: InvitationAcceptProps) {
  const preview = useInvitationPreview(token);
  const accept = useAcceptInvitation(token);

  if (preview.isPending) {
    return <p role="status">Загрузка приглашения...</p>;
  }
  if (preview.isError) {
    return (
      <div className="flex flex-col items-start gap-3">
        <FormError error={preview.error} />
        <Button type="button" variant="outline" onClick={() => preview.refetch()}>
          Повторить
        </Button>
      </div>
    );
  }

  const invitation = preview.data;
  return (
    <div className="flex flex-col gap-4">
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2">
        <dt className="text-muted-foreground">Организация</dt>
        <dd>{invitation.organization_name}</dd>
        <dt className="text-muted-foreground">Приглашение для</dt>
        <dd>{invitation.email}</dd>
        <dt className="text-muted-foreground">Роли</dt>
        <dd>
          {invitation.roles.length > 0 ? invitation.roles.map((role) => role.name).join(", ") : "—"}
        </dd>
        <dt className="text-muted-foreground">Действует до</dt>
        <dd>{formatDateTime(invitation.expires_at)}</dd>
      </dl>
      {invitation.status === "active" ? (
        <>
          {accept.error ? <FormError error={accept.error} /> : null}
          <Button
            type="button"
            disabled={accept.isPending}
            onClick={() => accept.mutate(undefined, { onSuccess: onAccepted })}
          >
            {accept.isPending ? "Принимаем..." : "Принять приглашение"}
          </Button>
        </>
      ) : (
        <p role="status" className="text-sm text-muted-foreground">
          {INACTIVE_MESSAGES[invitation.status]}
        </p>
      )}
    </div>
  );
}
