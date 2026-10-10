import { useState } from "react";

import type { MemberDto, RoleDto } from "@/shared/api/generated";
import { Button } from "@/shared/ui/button";
import { CheckboxGroup } from "@/shared/ui/checkbox-group";
import { FormError } from "@/shared/ui/form-error";

import { useRemoveMember, useUpdateMemberRoles } from "./api";

type MemberRowProps = {
  orgId: number;
  member: MemberDto;
  roles: RoleDto[];
  isSelf: boolean;
  canManage: boolean;
  onLeft: () => void;
};

export function MemberRow({ orgId, member, roles, isSelf, canManage, onLeft }: MemberRowProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [roleIds, setRoleIds] = useState<number[]>([]);
  const updateRoles = useUpdateMemberRoles(orgId);
  const removeMember = useRemoveMember(orgId);

  const canEditRoles = canManage && !member.is_creator;
  const canRemove = canManage && !member.is_creator && !isSelf;
  const canLeave = isSelf && !member.is_creator;

  function startEditing() {
    setRoleIds(member.roles.map((role) => role.id));
    setIsEditing(true);
  }

  function saveRoles() {
    updateRoles.mutate({ memberId: member.id, roleIds }, { onSuccess: () => setIsEditing(false) });
  }

  function remove(afterRemove?: () => void) {
    removeMember.mutate(member.id, { onSuccess: afterRemove });
  }

  return (
    <li className="flex flex-col gap-3 rounded-md border p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col">
          <span className="font-medium">
            {member.user.fullname}
            {isSelf ? " (вы)" : ""}
          </span>
          <span className="text-sm text-muted-foreground">{member.user.email}</span>
          <span className="mt-1 text-sm">
            {member.is_creator ? "Создатель" : null}
            {member.is_creator && member.roles.length > 0 ? ", " : null}
            {member.roles.map((role) => role.name).join(", ")}
            {!member.is_creator && member.roles.length === 0 ? (
              <span className="text-muted-foreground">Без ролей</span>
            ) : null}
          </span>
        </div>
        {isEditing ? null : (
          <div className="flex flex-wrap gap-2">
            {canEditRoles ? (
              <Button type="button" variant="outline" size="sm" onClick={startEditing}>
                Изменить роли
              </Button>
            ) : null}
            {canRemove ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={removeMember.isPending}
                onClick={() => remove()}
              >
                Исключить
              </Button>
            ) : null}
            {canLeave ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={removeMember.isPending}
                onClick={() => remove(onLeft)}
              >
                Выйти из организации
              </Button>
            ) : null}
          </div>
        )}
      </div>
      {isEditing ? (
        <div className="flex flex-col gap-3">
          {roles.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Ролей пока нет: их создаёт администратор системы.
            </p>
          ) : (
            <CheckboxGroup
              legend={`Роли: ${member.user.fullname}`}
              options={roles.map((role) => ({ value: role.id, label: role.name }))}
              value={roleIds}
              onChange={setRoleIds}
              disabled={updateRoles.isPending}
            />
          )}
          {updateRoles.error ? <FormError error={updateRoles.error} /> : null}
          <div className="flex gap-2">
            <Button type="button" size="sm" disabled={updateRoles.isPending} onClick={saveRoles}>
              {updateRoles.isPending ? "Сохраняем..." : "Сохранить"}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={updateRoles.isPending}
              onClick={() => setIsEditing(false)}
            >
              Отмена
            </Button>
          </div>
        </div>
      ) : null}
      {removeMember.error ? <FormError error={removeMember.error} /> : null}
    </li>
  );
}
