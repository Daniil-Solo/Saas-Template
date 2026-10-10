import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import type { InvitationCreatedDto } from "@/shared/api/generated";
import { Button } from "@/shared/ui/button";
import { CheckboxGroup } from "@/shared/ui/checkbox-group";
import { FieldError } from "@/shared/ui/field-error";
import { FormError } from "@/shared/ui/form-error";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

import { useCreateInvitation, useRoles } from "./api";
import { InvitationLink } from "./invitation-link";

const schema = z.object({
  email: z.string().trim().pipe(z.email("Введите корректный email")),
  role_ids: z.array(z.number()),
});
type FormValues = z.infer<typeof schema>;

type CreateInvitationFormProps = {
  orgId: number;
};

export function CreateInvitationForm({ orgId }: CreateInvitationFormProps) {
  const [created, setCreated] = useState<InvitationCreatedDto | null>(null);
  const { mutate, isPending, error } = useCreateInvitation(orgId);
  const roles = useRoles();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", role_ids: [] },
  });
  const { errors } = form.formState;

  function submit(values: FormValues) {
    setCreated(null);
    mutate(values, {
      onSuccess: (invitation) => {
        setCreated(invitation);
        form.reset();
      },
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={form.handleSubmit(submit)} className="flex flex-col gap-4" noValidate>
        <div className="flex flex-col gap-2">
          <Label htmlFor="invitation-email">Email приглашаемого</Label>
          <Input
            id="invitation-email"
            type="email"
            autoComplete="off"
            aria-invalid={errors.email ? true : undefined}
            {...form.register("email")}
          />
          <FieldError message={errors.email?.message} />
        </div>
        {roles.isPending ? <p role="status">Загрузка ролей...</p> : null}
        {roles.isError ? <FormError error={roles.error} /> : null}
        {roles.data && roles.data.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Ролей пока нет: приглашённый вступит без ролей.
          </p>
        ) : null}
        {roles.data && roles.data.length > 0 ? (
          <Controller
            control={form.control}
            name="role_ids"
            render={({ field }) => (
              <CheckboxGroup
                legend="Роли"
                options={roles.data.map((role) => ({ value: role.id, label: role.name }))}
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
        ) : null}
        {error ? <FormError error={error} /> : null}
        <Button type="submit" disabled={isPending}>
          {isPending ? "Создаём..." : "Создать приглашение"}
        </Button>
      </form>
      {created ? <InvitationLink token={created.token} email={created.email} /> : null}
    </div>
  );
}
