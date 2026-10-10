from enum import StrEnum


class InvitationStatus(StrEnum):
    """Хранимый статус приглашения. «Истекло» не хранится: это PENDING с expires_at в прошлом."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"


class InvitationDisplayStatus(StrEnum):
    """Статус приглашения для API: хранимый статус плюс вычисляемое «истекло»."""

    ACTIVE = "active"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"
