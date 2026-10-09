import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/shared/ui/button";
import { FieldError } from "@/shared/ui/field-error";
import { FormError } from "@/shared/ui/form-error";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

import { useLogin } from "./api";

const schema = z.object({
  email: z.string().trim().pipe(z.email("Введите корректный email")),
  password: z.string().min(1, "Введите пароль"),
});
type FormValues = z.infer<typeof schema>;

export function LoginForm() {
  const { mutate, isPending, error } = useLogin();
  const form = useForm<FormValues>({ resolver: zodResolver(schema) });
  const { errors } = form.formState;

  // После успешного входа токен сохраняется, и guard публичных маршрутов перенаправляет на /
  return (
    <form
      onSubmit={form.handleSubmit((values) => mutate(values))}
      className="flex flex-col gap-4"
      noValidate
    >
      <div className="flex flex-col gap-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          aria-invalid={errors.email ? true : undefined}
          {...form.register("email")}
        />
        <FieldError message={errors.email?.message} />
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="password">Пароль</Label>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          aria-invalid={errors.password ? true : undefined}
          {...form.register("password")}
        />
        <FieldError message={errors.password?.message} />
      </div>
      {error ? <FormError error={error} /> : null}
      <Button type="submit" disabled={isPending}>
        {isPending ? "Входим..." : "Войти"}
      </Button>
    </form>
  );
}
