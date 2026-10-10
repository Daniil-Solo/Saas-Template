import { CreateInvitationForm, InvitationsTable } from "@/features/invitations";

import { hasPermission, OrganizationShell } from "./organization-shell";

export function InvitationsPage() {
  return (
    <OrganizationShell>
      {(organization) =>
        hasPermission(organization, "invitations:manage") ? (
          <>
            <section aria-labelledby="invite-title" className="flex flex-col gap-3">
              <h2 id="invite-title" className="text-lg font-medium">
                Новое приглашение
              </h2>
              <CreateInvitationForm orgId={organization.id} />
            </section>
            <section aria-labelledby="invitations-title" className="flex flex-col gap-3">
              <h2 id="invitations-title" className="text-lg font-medium">
                Приглашения
              </h2>
              <InvitationsTable orgId={organization.id} />
            </section>
          </>
        ) : (
          <p role="alert">Нет доступа: для приглашений нужно право управлять приглашениями.</p>
        )
      }
    </OrganizationShell>
  );
}
