import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/shared/ui/button";
import { FieldError } from "@/shared/ui/field-error";
import { FormError } from "@/shared/ui/form-error";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

import { useRegister } from "./api";

const schema = z.object({
  fullname: z.string().trim().min(1, "Введите ФИО"),
  email: z.string().trim().pipe(z.email("Введите корректный email")),
  password: z
    .string()
    .min(8, "Пароль должен быть не короче 8 символов")
    .max(128, "Пароль должен быть не длиннее 128 символов"),
});
type FormValues = z.infer<typeof schema>;

type RegisterFormProps = {
  onSuccess: () => void;
};

export function RegisterForm({ onSuccess }: RegisterFormProps) {
  const { mutate, isPending, error } = useRegister();
  const form = useForm<FormValues>({ resolver: zodResolver(schema) });
  const { errors } = form.formState;

  return (
    <form
      onSubmit={form.handleSubmit((values) => mutate(values, { onSuccess }))}
      className="flex flex-col gap-4"
      noValidate
    >
      <div className="flex flex-col gap-2">
        <Label htmlFor="fullname">ФИО</Label>
        <Input
          id="fullname"
          autoComplete="name"
          aria-invalid={errors.fullname ? true : undefined}
          {...form.register("fullname")}
        />
        <FieldError message={errors.fullname?.message} />
      </div>
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
          autoComplete="new-password"
          aria-invalid={errors.password ? true : undefined}
          {...form.register("password")}
        />
        <FieldError message={errors.password?.message} />
      </div>
      {error ? <FormError error={error} /> : null}
      <Button type="submit" disabled={isPending}>
        {isPending ? "Регистрируем..." : "Зарегистрироваться"}
      </Button>
    </form>
  );
}
