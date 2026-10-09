import type { UserDto } from "@/shared/api/generated";

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
