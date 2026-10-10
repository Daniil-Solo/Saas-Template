import { useState } from "react";

import { Button } from "@/shared/ui/button";

type InvitationLinkProps = {
  token: string;
  email: string;
};

/** Ссылка-приглашение: токен backend отдаёт один раз, поэтому показываем её сразу после создания. */
export function InvitationLink({ token, email }: InvitationLinkProps) {
  const [copied, setCopied] = useState(false);
  const link = `${window.location.origin}/invitations/${token}`;

  async function copy() {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-md border bg-muted/40 p-3">
      <p className="text-sm">
        Приглашение для {email} создано. Ссылка показывается один раз — передайте её сами:
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <input
          readOnly
          aria-label="Ссылка-приглашение"
          value={link}
          className="h-9 min-w-0 flex-1 rounded-md border border-input bg-background px-3 text-sm"
          onFocus={(event) => event.currentTarget.select()}
        />
        <Button type="button" variant="outline" onClick={copy}>
          {copied ? "Скопировано" : "Копировать"}
        </Button>
      </div>
    </div>
  );
}
