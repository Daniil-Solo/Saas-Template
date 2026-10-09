import { Link } from "react-router";

export function NotFoundPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-4">
      <h1 className="text-2xl font-semibold">Страница не найдена</h1>
      <Link to="/" className="underline underline-offset-4">
        На главную
      </Link>
    </main>
  );
}
