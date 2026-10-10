from abc import ABC, abstractmethod

from src.dto.organizations import OrganizationDTO


class OrganizationsDAO(ABC):
    @abstractmethod
    async def create(self, name: str, created_by_id: int) -> OrganizationDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, organization_id: int) -> OrganizationDTO:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(self, user_id: int) -> list[OrganizationDTO]:
        """Организации, в которых пользователь состоит участником."""
        raise NotImplementedError
