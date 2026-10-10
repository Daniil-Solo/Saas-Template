from abc import ABC, abstractmethod

from src.dto.roles import RoleCreateDTO, RoleDTO, RoleUpdateDTO


class RolesDAO(ABC):
    @abstractmethod
    async def create(self, data: RoleCreateDTO) -> RoleDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, role_id: int) -> RoleDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> list[RoleDTO]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_ids(self, role_ids: list[int]) -> list[RoleDTO]:
        """Возвращает найденные роли; несуществующие id в результат не попадают."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, role_id: int, data: RoleUpdateDTO) -> RoleDTO:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, role_id: int) -> None:
        raise NotImplementedError
