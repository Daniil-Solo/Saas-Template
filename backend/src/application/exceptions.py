class ApplicationError(Exception):
    """Базовая бизнес-ошибка. В HTTP-коды превращается в src/interfaces/api/error_status_mapping.py."""

    code = "application_error"
    default_message = "Ошибка приложения"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(ApplicationError):
    code = "not_found"
    default_message = "Объект не найден"


class ConflictError(ApplicationError):
    code = "conflict"
    default_message = "Конфликт данных"


class UnauthorizedError(ApplicationError):
    code = "unauthorized"
    default_message = "Требуется аутентификация"


class UserNotFoundError(NotFoundError):
    code = "user_not_found"
    default_message = "Пользователь не найден"


class UserEmailExistsError(ConflictError):
    code = "user_email_exists"
    default_message = "Пользователь с таким email уже существует"


class InvalidCredentialsError(UnauthorizedError):
    code = "invalid_credentials"
    default_message = "Неверный email или пароль"


class InvalidTokenError(UnauthorizedError):
    code = "invalid_token"
    default_message = "Токен отсутствует, просрочен или некорректен"
