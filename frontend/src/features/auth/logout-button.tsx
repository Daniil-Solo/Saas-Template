import { LogOut } from "lucide-react";

import { Button } from "@/shared/ui/button";

import { useLogout } from "./api";

export function LogoutButton() {
  const logout = useLogout();

  return (
    <Button type="button" variant="outline" onClick={logout}>
      <LogOut aria-hidden="true" />
      Выйти
    </Button>
  );
}
