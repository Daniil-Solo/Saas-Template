import { getErrorMessage } from "@/shared/api";

type FormErrorProps = {
  error: unknown;
};

export function FormError({ error }: FormErrorProps) {
  return (
    <p
      role="alert"
      className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
    >
      {getErrorMessage(error)}
    </p>
  );
}
