import { LogoutButton, UserProfile } from "@/features/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";

export function HomePage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>
            <h1>Профиль</h1>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <UserProfile />
          <LogoutButton />
        </CardContent>
      </Card>
    </main>
  );
}
