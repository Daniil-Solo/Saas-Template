import { Button } from "@/shared/ui/button";
import { FormError } from "@/shared/ui/form-error";

import { useMembers, useRoles } from "./api";
import { MemberRow } from "./member-row";

type MembersListProps = {
  orgId: number;
  currentUserId: number | undefined;
  /** Право «Управление участниками» (или создатель) - из деталей организации. */
  canManage: boolean;
  onLeft: () => void;
};

export function MembersList({ orgId, currentUserId, canManage, onLeft }: MembersListProps) {
  const members = useMembers(orgId);
  // Роли нужны только для смены ролей, поэтому не запрашиваем их тем, кто менять не может
  const roles = useRoles(canManage);

  if (members.isPending) {
    return <p role="status">Загрузка участников...</p>;
  }
  if (members.isError) {
    return (
      <div className="flex flex-col items-start gap-3">
        <FormError error={members.error} />
        <Button type="button" variant="outline" onClick={() => members.refetch()}>
          Повторить
        </Button>
      </div>
    );
  }
  if (members.data.length === 0) {
    return <p className="text-sm text-muted-foreground">В организации пока нет участников.</p>;
  }
  return (
    <ul className="flex flex-col gap-3">
      {members.data.map((member) => (
        <MemberRow
          key={member.id}
          orgId={orgId}
          member={member}
          roles={roles.data ?? []}
          isSelf={member.user.id === currentUserId}
          canManage={canManage}
          onLeft={onLeft}
        />
      ))}
    </ul>
  );
}
