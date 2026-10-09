from typing import Any

from httpx import AsyncClient
from pydantic import BaseModel


class BaseEndpoints:
    """Базовый класс группы эндпоинтов. Методы наследников принимают параметры запроса и возвращают Response."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    @staticmethod
    def to_json(data: BaseModel | dict[str, Any]) -> dict[str, Any]:
        # dict нужен для проверки невалидных payload, которые нельзя собрать через DTO
        if isinstance(data, BaseModel):
            return data.model_dump(mode="json", by_alias=True)
        return data

    @staticmethod
    def bearer_headers(token: str | None, scheme: str = "Bearer") -> dict[str, str]:
        if token is None:
            return {}
        return {"Authorization": f"{scheme} {token}"}
