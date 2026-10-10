import { useNavigate, useParams } from "react-router";

import { InvitationAccept } from "@/features/invitations";
import { setLastOrganizationId } from "@/features/organizations";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";

export function InvitationPage() {
  const { token } = useParams();
  const navigate = useNavigate();

  return (
    <main className="flex justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>
            <h1>Приглашение в организацию</h1>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {token ? (
            <InvitationAccept
              token={token}
              onAccepted={(organization) => {
                setLastOrganizationId(organization.id);
                navigate(`/organizations/${organization.id}/members`);
              }}
            />
          ) : (
            <p role="alert">Приглашение не найдено</p>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
