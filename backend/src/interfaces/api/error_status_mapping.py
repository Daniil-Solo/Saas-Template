from fastapi import status

from src.application.exceptions import (
    ApplicationError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)

# Ищется по иерархии классов: UserEmailExistsError -> ConflictError -> 409
ERROR_STATUS_MAPPING: dict[type[ApplicationError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
    ApplicationError: status.HTTP_400_BAD_REQUEST,
}


def get_status_code(error: ApplicationError) -> int:
    for error_class in type(error).__mro__:
        if error_class in ERROR_STATUS_MAPPING:
            return ERROR_STATUS_MAPPING[error_class]
    return status.HTTP_400_BAD_REQUEST
