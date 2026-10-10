import { UserProfile } from "@/features/auth";
import { MyOrganizations } from "@/features/organizations";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";

export function HomePage() {
  return (
    <main className="flex flex-col items-center gap-4 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>
            <h1>Профиль</h1>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <UserProfile />
        </CardContent>
      </Card>
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>
            <h2>Мои организации</h2>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <MyOrganizations />
        </CardContent>
      </Card>
    </main>
  );
}
