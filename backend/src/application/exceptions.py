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


class ForbiddenError(ApplicationError):
    code = "forbidden"
    default_message = "Недостаточно прав"


class GoneError(ApplicationError):
    code = "gone"
    default_message = "Ресурс больше недоступен"


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


class OrganizationNotFoundError(NotFoundError):
    code = "organization_not_found"
    default_message = "Организация не найдена"


class PermissionDeniedError(ForbiddenError):
    code = "permission_denied"
    default_message = "Недостаточно прав для этого действия"


class AdminRequiredError(ForbiddenError):
    code = "admin_required"
    default_message = "Действие доступно только администратору системы"


class MemberNotFoundError(NotFoundError):
    code = "member_not_found"
    default_message = "Участник не найден"


class OrganizationCreatorCannotLeaveError(ConflictError):
    code = "organization_creator_cannot_leave"
    default_message = "Создатель не может покинуть организацию или быть исключён из неё"


class InvitationNotFoundError(NotFoundError):
    code = "invitation_not_found"
    default_message = "Приглашение не найдено"


class InvitationExpiredError(GoneError):
    code = "invitation_expired"
    default_message = "Срок действия приглашения истёк"


class InvitationNotPendingError(ConflictError):
    code = "invitation_not_pending"
    default_message = "Приглашение уже принято или отозвано"


class InvitationEmailMismatchError(ForbiddenError):
    code = "invitation_email_mismatch"
    default_message = "Приглашение выдано на другой email"


class InvitationAlreadyExistsError(ConflictError):
    code = "invitation_already_exists"
    default_message = "На этот email уже есть действующее приглашение"


class MemberAlreadyExistsError(ConflictError):
    code = "member_already_exists"
    default_message = "Пользователь уже состоит в организации"


class RoleNotFoundError(NotFoundError):
    code = "role_not_found"
    default_message = "Роль не найдена"


class RoleNameExistsError(ConflictError):
    code = "role_name_exists"
    default_message = "Роль с таким названием уже существует"
