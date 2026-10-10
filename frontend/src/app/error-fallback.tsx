import { Button } from "@/shared/ui/button";

export function ErrorFallback() {
  return (
    <div role="alert" className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
      <h1 className="text-xl font-semibold">Что-то пошло не так</h1>
      <p className="text-muted-foreground">
        Мы уже знаем об ошибке. Попробуйте перезагрузить страницу.
      </p>
      <Button type="button" onClick={() => window.location.reload()}>
        Перезагрузить
      </Button>
    </div>
  );
}
