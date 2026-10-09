from typing import Any

from fastapi import status
from httpx import Response
from pydantic import TypeAdapter


class ResponseWrapper[T]:
    """Ответ эндпоинта с типизированной проверкой.

    - `validate()` проверяет успешный статус и возвращает тело, разобранное в DTO;
    - `expected_error_status(...)` и `expect_validation_error(...)` проверяют ожидаемую ошибку.

    Сырой ответ остается доступен (`response`, `status_code`, `headers`, `json()`) для специфичных проверок.
    Для списков передавайте `TypeAdapter(list[SomeDTO])`.
    """

    def __init__(
        self,
        response: Response,
        dto_type: type[T] | TypeAdapter[T],
        success_status: int = status.HTTP_200_OK,
    ) -> None:
        self._response = response
        self._adapter: TypeAdapter[T] = dto_type if isinstance(dto_type, TypeAdapter) else TypeAdapter(dto_type)
        self._success_status = success_status

    @property
    def response(self) -> Response:
        return self._response

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def headers(self) -> Any:
        return self._response.headers

    def json(self) -> Any:
        return self._response.json()

    def validate(self) -> T:
        self._assert_status(self._success_status)
        return self._adapter.validate_json(self._response.text)

    def expected_error_status(self, status_code: int, code: str | None = None) -> Response:
        """Ожидает ошибку бизнес-слоя: проверяет HTTP-статус и (если передан) поле `code` в теле."""
        self._assert_status(status_code)
        if code is not None:
            actual_code = self._response.json().get("code")
            assert actual_code == code, f"Ожидался code={code!r}, получен {actual_code!r}: {self._response.text}"
        return self._response

    def expect_validation_error(self, message: str | None = None, field: str | None = None) -> Response:
        """Ожидает 422: опционально проверяет подстроку в тексте ошибки и имя поля (последний элемент `loc`)."""
        self._assert_status(status.HTTP_422_UNPROCESSABLE_CONTENT)
        details: list[dict[str, Any]] = self._response.json()["detail"]
        if field is not None:
            fields = [detail["loc"][-1] for detail in details]
            assert field in fields, f"Ожидалась ошибка поля {field!r}, получены {fields}: {self._response.text}"
        if message is not None:
            messages = [detail["msg"] for detail in details]
            assert any(message in msg for msg in messages), f"Ожидалось сообщение с {message!r}, получены {messages}"
        return self._response

    def _assert_status(self, expected: int) -> None:
        assert self._response.status_code == expected, (
            f"Ожидался статус {expected}, получен {self._response.status_code}: {self._response.text}"
        )
