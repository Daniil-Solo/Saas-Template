import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { OrganizationDto } from "@/shared/api/generated";
import { Button } from "@/shared/ui/button";
import { FieldError } from "@/shared/ui/field-error";
import { FormError } from "@/shared/ui/form-error";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

import { useCreateOrganization } from "./api";
import { setLastOrganizationId } from "./last-organization";

const schema = z.object({
  name: z.string().trim().min(1, "Введите название").max(255, "Не длиннее 255 символов"),
});
type FormValues = z.infer<typeof schema>;

type CreateOrganizationFormProps = {
  onSuccess: (organization: OrganizationDto) => void;
};

export function CreateOrganizationForm({ onSuccess }: CreateOrganizationFormProps) {
  const { mutate, isPending, error } = useCreateOrganization();
  const form = useForm<FormValues>({ resolver: zodResolver(schema) });
  const { errors } = form.formState;

  function submit(values: FormValues) {
    mutate(values, {
      onSuccess: (organization) => {
        setLastOrganizationId(organization.id);
        onSuccess(organization);
      },
    });
  }

  return (
    <form onSubmit={form.handleSubmit(submit)} className="flex flex-col gap-4" noValidate>
      <div className="flex flex-col gap-2">
        <Label htmlFor="organization-name">Название</Label>
        <Input
          id="organization-name"
          autoComplete="organization"
          aria-invalid={errors.name ? true : undefined}
          {...form.register("name")}
        />
        <FieldError message={errors.name?.message} />
      </div>
      {error ? <FormError error={error} /> : null}
      <Button type="submit" disabled={isPending}>
        {isPending ? "Создаём..." : "Создать организацию"}
      </Button>
    </form>
  );
}
