import type { ReactNode } from "react";
import { useEffect } from "react";
import { Link, NavLink, useParams } from "react-router";

import { setLastOrganizationId, useOrganization } from "@/features/organizations";
import type { OrganizationDetailDto, Permission } from "@/shared/api/generated";
import { parseIdParam } from "@/shared/lib/ids";
import { Button } from "@/shared/ui/button";
import { FormError } from "@/shared/ui/form-error";

/** Есть ли у пользователя право в организации (создатель может всё). Окончательную проверку делает backend. */
export function hasPermission(organization: OrganizationDetailDto, permission: Permission) {
  return organization.is_creator || organization.permissions.includes(permission);
}

type OrganizationShellProps = {
  children: (organization: OrganizationDetailDto) => ReactNode;
};

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? "font-medium underline underline-offset-4" : "text-muted-foreground";

/** Общая часть страниц `/organizations/:orgId/*`: загрузка организации, состояния экрана, заголовок и меню. */
export function OrganizationShell({ children }: OrganizationShellProps) {
  const orgId = parseIdParam(useParams().orgId);
  const { data: organization, isPending, isError, error, refetch } = useOrganization(orgId);

  useEffect(() => {
    if (organization) {
      setLastOrganizationId(organization.id);
    }
  }, [organization]);

  if (orgId === null) {
    return (
      <main className="mx-auto flex max-w-3xl flex-col items-start gap-3 p-4">
        <p role="alert">Организация не найдена</p>
        <Link to="/" className="underline underline-offset-4">
          На главную
        </Link>
      </main>
    );
  }
  if (isPending) {
    return (
      <main className="mx-auto max-w-3xl p-4">
        <p role="status">Загрузка организации...</p>
      </main>
    );
  }
  if (isError) {
    return (
      <main className="mx-auto flex max-w-3xl flex-col items-start gap-3 p-4">
        <FormError error={error} />
        <Button type="button" variant="outline" onClick={() => refetch()}>
          Повторить
        </Button>
        <Link to="/" className="underline underline-offset-4">
          На главную
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-4 p-4">
      <h1 className="text-2xl font-semibold">{organization.name}</h1>
      <nav aria-label="Разделы организации" className="flex gap-4 text-sm">
        <NavLink to={`/organizations/${organization.id}/members`} className={navLinkClass}>
          Участники
        </NavLink>
        {hasPermission(organization, "invitations:manage") ? (
          <NavLink to={`/organizations/${organization.id}/invitations`} className={navLinkClass}>
            Приглашения
          </NavLink>
        ) : null}
      </nav>
      {children(organization)}
    </main>
  );
}
