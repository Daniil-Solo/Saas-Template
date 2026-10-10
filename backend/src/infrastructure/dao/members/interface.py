from abc import ABC, abstractmethod

from src.dto.organizations import MemberDTO, OrganizationAccessDTO


class MembersDAO(ABC):
    @abstractmethod
    async def create(self, organization_id: int, user_id: int) -> int:
        """Добавляет участника без ролей, возвращает его id. Дубль -> MemberAlreadyExistsError."""
        raise NotImplementedError

    @abstractmethod
    async def get_access(self, organization_id: int, user_id: int) -> OrganizationAccessDTO:
        """Доступ пользователя к организации. Не участник -> OrganizationNotFoundError."""
        raise NotImplementedError

    @abstractmethod
    async def get(self, organization_id: int, member_id: int) -> MemberDTO:
        raise NotImplementedError

    @abstractmethod
    async def list_for_organization(self, organization_id: int) -> list[MemberDTO]:
        raise NotImplementedError

    @abstractmethod
    async def exists_by_email(self, organization_id: int, email: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def set_roles(self, member_id: int, role_ids: list[int]) -> None:
        """Заменяет набор ролей участника."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, member_id: int) -> None:
        raise NotImplementedError
