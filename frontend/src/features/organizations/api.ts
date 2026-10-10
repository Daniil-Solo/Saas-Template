import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { OrganizationCreateDto } from "@/shared/api/generated";
import {
  createOrganizationEndpointApiV1OrganizationsPost,
  getOrganizationEndpointApiV1OrganizationsOrgIdGet,
  listMembersEndpointApiV1OrganizationsOrgIdMembersGet,
  listOrganizationsEndpointApiV1OrganizationsGet,
  listRolesEndpointApiV1RolesGet,
  removeMemberEndpointApiV1OrganizationsOrgIdMembersMemberIdDelete,
  updateMemberRolesEndpointApiV1OrganizationsOrgIdMembersMemberIdRolesPut,
} from "@/shared/api/generated";

// Все ключи организаций начинаются с "organizations": одна инвалидация обновляет и список, и детали
export const organizationsKey = ["organizations"] as const;
export const organizationKey = (orgId: number) => ["organizations", orgId] as const;
export const membersKey = (orgId: number) => ["organizations", orgId, "members"] as const;
export const rolesKey = ["roles"] as const;

export function useOrganizations() {
  return useQuery({
    queryKey: organizationsKey,
    queryFn: async () =>
      (await listOrganizationsEndpointApiV1OrganizationsGet({ throwOnError: true })).data,
  });
}

/** Детали организации с правами текущего пользователя (`permissions`, `is_creator`). */
export function useOrganization(orgId: number | null) {
  return useQuery({
    queryKey: organizationKey(orgId ?? 0),
    queryFn: async () =>
      (
        await getOrganizationEndpointApiV1OrganizationsOrgIdGet({
          path: { org_id: orgId ?? 0 },
          throwOnError: true,
        })
      ).data,
    enabled: orgId !== null,
  });
}

export function useCreateOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: OrganizationCreateDto) =>
      (await createOrganizationEndpointApiV1OrganizationsPost({ body, throwOnError: true })).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: organizationsKey }),
  });
}

export function useMembers(orgId: number) {
  return useQuery({
    queryKey: membersKey(orgId),
    queryFn: async () =>
      (
        await listMembersEndpointApiV1OrganizationsOrgIdMembersGet({
          path: { org_id: orgId },
          throwOnError: true,
        })
      ).data,
  });
}

export function useRoles(enabled = true) {
  return useQuery({
    queryKey: rolesKey,
    queryFn: async () => (await listRolesEndpointApiV1RolesGet({ throwOnError: true })).data,
    enabled,
  });
}

export function useUpdateMemberRoles(orgId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ memberId, roleIds }: { memberId: number; roleIds: number[] }) =>
      (
        await updateMemberRolesEndpointApiV1OrganizationsOrgIdMembersMemberIdRolesPut({
          path: { org_id: orgId, member_id: memberId },
          body: { role_ids: roleIds },
          throwOnError: true,
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: membersKey(orgId) }),
  });
}

/** Исключение участника и выход из организации (участник удаляет сам себя). */
export function useRemoveMember(orgId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (memberId: number) =>
      (
        await removeMemberEndpointApiV1OrganizationsOrgIdMembersMemberIdDelete({
          path: { org_id: orgId, member_id: memberId },
          throwOnError: true,
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: organizationsKey }),
  });
}
