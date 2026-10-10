import { useNavigate } from "react-router";

import { CreateOrganizationForm } from "@/features/organizations";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

export function OrganizationNewPage() {
  const navigate = useNavigate();

  return (
    <main className="flex justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>
            <h1>Новая организация</h1>
          </CardTitle>
          <CardDescription>Вы станете её создателем</CardDescription>
        </CardHeader>
        <CardContent>
          <CreateOrganizationForm
            onSuccess={(organization) => navigate(`/organizations/${organization.id}/members`)}
          />
        </CardContent>
      </Card>
    </main>
  );
}
