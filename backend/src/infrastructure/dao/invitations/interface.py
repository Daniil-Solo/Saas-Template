from abc import ABC, abstractmethod
import datetime

from src.dto.invitations import InvitationRecordDTO
from src.dto.roles import RoleDTO


class InvitationsDAO(ABC):
    @abstractmethod
    async def create(
        self,
        organization_id: int,
        email: str,
        token_hash: str,
        expires_at: datetime.datetime,
        invited_by_id: int,
        role_ids: list[int],
    ) -> InvitationRecordDTO:
        """Создаёт приглашение со статусом pending. Дубль действующего -> InvitationAlreadyExistsError."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, organization_id: int, invitation_id: int) -> InvitationRecordDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str, for_update: bool = False) -> InvitationRecordDTO:
        """Приглашение по хешу токена; for_update блокирует строку до конца транзакции."""
        raise NotImplementedError

    @abstractmethod
    async def list_for_organization(self, organization_id: int) -> list[InvitationRecordDTO]:
        raise NotImplementedError

    @abstractmethod
    async def get_roles(self, invitation_ids: list[int]) -> dict[int, list[RoleDTO]]:
        """Роли приглашений (существующие на данный момент), ключ - id приглашения."""
        raise NotImplementedError

    @abstractmethod
    async def get_role_ids(self, invitation_id: int) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    async def revoke_expired_pending(self, organization_id: int, email: str, now: datetime.datetime) -> None:
        """Переводит просроченные pending-приглашения на email в revoked."""
        raise NotImplementedError

    @abstractmethod
    async def mark_revoked(self, invitation_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_accepted(self, invitation_id: int, accepted_at: datetime.datetime) -> None:
        raise NotImplementedError
