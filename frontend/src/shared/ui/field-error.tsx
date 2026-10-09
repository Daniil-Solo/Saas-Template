type FieldErrorProps = {
  message: string | undefined;
};

export function FieldError({ message }: FieldErrorProps) {
  if (!message) {
    return null;
  }
  return (
    <p role="alert" className="text-sm text-destructive">
      {message}
    </p>
  );
}
