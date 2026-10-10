from enum import StrEnum


class Permission(StrEnum):
    MEMBERS_MANAGE = "members:manage"
    INVITATIONS_MANAGE = "invitations:manage"
