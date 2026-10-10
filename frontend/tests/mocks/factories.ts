import type {
  InvitationDto,
  MemberDto,
  OrganizationDetailDto,
  OrganizationDto,
  RoleDto,
  UserDto,
} from "@/shared/api/generated";

export function makeUser(overrides: Partial<UserDto> = {}): UserDto {
  return {
    id: 1,
    fullname: "Иван Петров",
    email: "ivan@example.com",
    is_verified: true,
    is_admin: false,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

export function makeRole(overrides: Partial<RoleDto> = {}): RoleDto {
  return {
    id: 1,
    name: "Менеджер",
    permissions: ["members:manage"],
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

export function makeOrganization(overrides: Partial<OrganizationDto> = {}): OrganizationDto {
  return {
    id: 1,
    name: "Acme",
    created_by_id: 1,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

export function makeOrganizationDetail(
  overrides: Partial<OrganizationDetailDto> = {},
): OrganizationDetailDto {
  return {
    ...makeOrganization(),
    permissions: ["members:manage", "invitations:manage"],
    is_creator: true,
    ...overrides,
  };
}

export function makeMember(overrides: Partial<MemberDto> = {}): MemberDto {
  return {
    id: 1,
    organization_id: 1,
    user: { id: 1, fullname: "Иван Петров", email: "ivan@example.com" },
    roles: [],
    is_creator: true,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

export function makeInvitation(overrides: Partial<InvitationDto> = {}): InvitationDto {
  return {
    id: 1,
    organization_id: 1,
    email: "anna@example.com",
    status: "active",
    roles: [],
    expires_at: "2026-12-31T00:00:00Z",
    invited_by_id: 1,
    created_at: "2026-01-01T00:00:00Z",
    accepted_at: null,
    ...overrides,
  };
}
