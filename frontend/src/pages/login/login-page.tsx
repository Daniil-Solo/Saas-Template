import { Link, useLocation } from "react-router";
import { z } from "zod";

import { LoginForm } from "@/features/auth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

const registeredStateSchema = z.object({ registered: z.literal(true) });

export function LoginPage() {
  const location = useLocation();
  const justRegistered = registeredStateSchema.safeParse(location.state).success;

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>
            <h1>Вход</h1>
          </CardTitle>
          <CardDescription>Войдите по email и паролю</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {justRegistered ? (
            <p role="status" className="text-sm text-muted-foreground">
              Регистрация прошла успешно. Теперь войдите.
            </p>
          ) : null}
          <LoginForm />
          <p className="text-center text-sm text-muted-foreground">
            Нет аккаунта?{" "}
            <Link to="/register" className="text-foreground underline underline-offset-4">
              Зарегистрироваться
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
