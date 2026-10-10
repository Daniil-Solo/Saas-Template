import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { InvitationCreateDto } from "@/shared/api/generated";
import {
  acceptInvitationEndpointApiV1InvitationsTokenAcceptPost,
  createInvitationEndpointApiV1OrganizationsOrgIdInvitationsPost,
  listInvitationsEndpointApiV1OrganizationsOrgIdInvitationsGet,
  listRolesEndpointApiV1RolesGet,
  previewInvitationEndpointApiV1InvitationsTokenGet,
  revokeInvitationEndpointApiV1OrganizationsOrgIdInvitationsInvitationIdDelete,
} from "@/shared/api/generated";

export const invitationsKey = (orgId: number) => ["invitations", orgId] as const;
export const invitationPreviewKey = (token: string) => ["invitations", "preview", token] as const;
// Ключи ниже принадлежат feature organizations; здесь они нужны только для инвалидации
const organizationsKey = ["organizations"] as const;
const rolesKey = ["roles"] as const;

export function useRoles() {
  return useQuery({
    queryKey: rolesKey,
    queryFn: async () => (await listRolesEndpointApiV1RolesGet({ throwOnError: true })).data,
  });
}

export function useInvitations(orgId: number) {
  return useQuery({
    queryKey: invitationsKey(orgId),
    queryFn: async () =>
      (
        await listInvitationsEndpointApiV1OrganizationsOrgIdInvitationsGet({
          path: { org_id: orgId },
          throwOnError: true,
        })
      ).data,
  });
}

export function useCreateInvitation(orgId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: InvitationCreateDto) =>
      (
        await createInvitationEndpointApiV1OrganizationsOrgIdInvitationsPost({
          path: { org_id: orgId },
          body,
          throwOnError: true,
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: invitationsKey(orgId) }),
  });
}

export function useRevokeInvitation(orgId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (invitationId: number) =>
      (
        await revokeInvitationEndpointApiV1OrganizationsOrgIdInvitationsInvitationIdDelete({
          path: { org_id: orgId, invitation_id: invitationId },
          throwOnError: true,
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: invitationsKey(orgId) }),
  });
}

export function useInvitationPreview(token: string) {
  return useQuery({
    queryKey: invitationPreviewKey(token),
    queryFn: async () =>
      (
        await previewInvitationEndpointApiV1InvitationsTokenGet({
          path: { token },
          throwOnError: true,
        })
      ).data,
  });
}

export function useAcceptInvitation(token: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () =>
      (
        await acceptInvitationEndpointApiV1InvitationsTokenAcceptPost({
          path: { token },
          throwOnError: true,
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: organizationsKey }),
  });
}
