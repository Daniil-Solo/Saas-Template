import { useMatch, useNavigate } from "react-router";

import { parseIdParam } from "@/shared/lib/ids";

import { useOrganizations } from "./api";
import { getLastOrganizationId, setLastOrganizationId } from "./last-organization";

const NEW_ORGANIZATION = "new";

/** Выпадающий список организаций в шапке: выбор текущей и переход к созданию новой. */
export function OrganizationSwitcher() {
  const { data: organizations, isPending, isError } = useOrganizations();
  const navigate = useNavigate();
  const match = useMatch("/organizations/:orgId/*");
  const currentId = parseIdParam(match?.params.orgId) ?? getLastOrganizationId();

  if (isPending) {
    return <p role="status">Загрузка организаций...</p>;
  }
  if (isError) {
    return <p className="text-sm text-destructive">Не удалось загрузить организации</p>;
  }

  const selected = organizations.some((organization) => organization.id === currentId)
    ? String(currentId)
    : "";

  function change(value: string) {
    if (value === NEW_ORGANIZATION) {
      navigate("/organizations/new");
      return;
    }
    const orgId = parseIdParam(value);
    if (orgId !== null) {
      setLastOrganizationId(orgId);
      navigate(`/organizations/${orgId}/members`);
    }
  }

  return (
    <select
      aria-label="Организация"
      className="h-9 rounded-md border border-input bg-background px-3 text-sm"
      value={selected}
      onChange={(event) => change(event.target.value)}
    >
      <option value="" disabled>
        {organizations.length === 0 ? "Нет организаций" : "Выберите организацию"}
      </option>
      {organizations.map((organization) => (
        <option key={organization.id} value={organization.id}>
          {organization.name}
        </option>
      ))}
      <option value={NEW_ORGANIZATION}>+ Создать организацию</option>
    </select>
  );
}
