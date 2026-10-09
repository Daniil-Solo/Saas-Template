from abc import ABC, abstractmethod

from src.dto.users import UserCreateDTO, UserDTO, UserWithPasswordDTO


class UsersDAO(ABC):
    @abstractmethod
    async def create(self, data: UserCreateDTO) -> UserDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: int) -> UserDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> UserWithPasswordDTO:
        raise NotImplementedError

    @abstractmethod
    async def update_hashed_password(self, user_id: int, hashed_password: str) -> None:
        raise NotImplementedError
