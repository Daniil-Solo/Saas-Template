import { Link, Outlet } from "react-router";

import { LogoutButton } from "@/features/auth";
import { OrganizationSwitcher } from "@/features/organizations";

/** Общая оболочка приватных страниц: шапка с переключателем организаций и выходом. */
export function AppLayout() {
  return (
    <>
      <header className="flex flex-wrap items-center gap-3 border-b px-4 py-3">
        <Link to="/" className="font-semibold">
          Главная
        </Link>
        <OrganizationSwitcher />
        <div className="ml-auto">
          <LogoutButton />
        </div>
      </header>
      <Outlet />
    </>
  );
}
