import { useNavigate } from "react-router";

import { useCurrentUser } from "@/features/auth";
import { clearLastOrganizationId, MembersList } from "@/features/organizations";

import { hasPermission, OrganizationShell } from "./organization-shell";

export function MembersPage() {
  const navigate = useNavigate();
  const { data: currentUser } = useCurrentUser();

  return (
    <OrganizationShell>
      {(organization) => (
        <section aria-labelledby="members-title" className="flex flex-col gap-3">
          <h2 id="members-title" className="text-lg font-medium">
            Участники
          </h2>
          <MembersList
            orgId={organization.id}
            currentUserId={currentUser?.id}
            canManage={hasPermission(organization, "members:manage")}
            onLeft={() => {
              clearLastOrganizationId();
              navigate("/");
            }}
          />
        </section>
      )}
    </OrganizationShell>
  );
}
