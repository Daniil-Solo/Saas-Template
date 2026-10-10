import { Link } from "react-router";

import { Button } from "@/shared/ui/button";
import { FormError } from "@/shared/ui/form-error";

import { useOrganizations } from "./api";
import { setLastOrganizationId } from "./last-organization";

/** Блок «Мои организации» на главной странице. */
export function MyOrganizations() {
  const { data: organizations, isPending, isError, error, refetch } = useOrganizations();

  if (isPending) {
    return <p role="status">Загрузка организаций...</p>;
  }
  if (isError) {
    return (
      <div className="flex flex-col items-start gap-3">
        <FormError error={error} />
        <Button type="button" variant="outline" onClick={() => refetch()}>
          Повторить
        </Button>
      </div>
    );
  }
  if (organizations.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        У вас пока нет организаций.{" "}
        <Link to="/organizations/new" className="text-foreground underline underline-offset-4">
          Создать организацию
        </Link>
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-3">
      <ul className="flex flex-col gap-1">
        {organizations.map((organization) => (
          <li key={organization.id}>
            <Link
              to={`/organizations/${organization.id}/members`}
              onClick={() => setLastOrganizationId(organization.id)}
              className="underline underline-offset-4"
            >
              {organization.name}
            </Link>
          </li>
        ))}
      </ul>
      <Link
        to="/organizations/new"
        className="text-sm text-muted-foreground underline underline-offset-4"
      >
        Создать организацию
      </Link>
    </div>
  );
}
