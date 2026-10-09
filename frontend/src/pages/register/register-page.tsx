import { Link, useNavigate } from "react-router";

import { RegisterForm } from "@/features/auth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

export function RegisterPage() {
  const navigate = useNavigate();

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>
            <h1>Регистрация</h1>
          </CardTitle>
          <CardDescription>Создайте аккаунт</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <RegisterForm onSuccess={() => navigate("/login", { state: { registered: true } })} />
          <p className="text-center text-sm text-muted-foreground">
            Уже есть аккаунт?{" "}
            <Link to="/login" className="text-foreground underline underline-offset-4">
              Войти
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
