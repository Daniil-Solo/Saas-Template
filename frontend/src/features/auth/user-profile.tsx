import { Button } from "@/shared/ui/button";
import { FormError } from "@/shared/ui/form-error";

import { useCurrentUser } from "./api";

export function UserProfile() {
  const { data: user, isPending, isError, error, refetch } = useCurrentUser();

  if (isPending) {
    return <p role="status">Загрузка профиля...</p>;
  }
  if (isError) {
    return (
      <div className="flex flex-col items-start gap-3">
        <FormError error={error} />
        <Button type="button" variant="outline" onClick={() => refetch()}>
          Повторить
        </Button>
      </div>
    );
  }
  // Пустого состояния у профиля нет: backend всегда возвращает текущего пользователя.
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2">
      <dt className="text-muted-foreground">ФИО</dt>
      <dd>{user.fullname}</dd>
      <dt className="text-muted-foreground">Email</dt>
      <dd>{user.email}</dd>
    </dl>
  );
}
