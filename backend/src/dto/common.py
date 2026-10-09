from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SuccessOperationDTO(BaseDTO):
    message: str = Field(default="", description="Сообщение о результате операции")


class ErrorDTO(BaseDTO):
    code: str = Field(description="Машиночитаемый код ошибки")
    message: str = Field(description="Описание ошибки")


def _normalize_email(value: object) -> object:
    if isinstance(value, str):
        return value.strip().lower()
    return value


# Email хранится и сравнивается в нижнем регистре, поэтому нормализуем его на входе
NormalizedEmail = Annotated[EmailStr, BeforeValidator(_normalize_email)]
