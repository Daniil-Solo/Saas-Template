import { z } from "zod";

const errorBodySchema = z.object({ code: z.string(), message: z.string() });
const validationBodySchema = z.object({ detail: z.array(z.unknown()) });

// Тексты для известных кодов ошибок backend (docs/usecases/auth.md, docs/usecases/organizations.md)
const MESSAGES_BY_CODE: Record<string, string> = {
  user_email_exists: "Пользователь с таким email уже существует",
  invalid_credentials: "Неверный email или пароль",
  invalid_token: "Сессия истекла. Войдите снова",
  organization_not_found: "Организация не найдена",
  permission_denied: "Недостаточно прав для этого действия",
  admin_required: "Действие доступно только администратору",
  member_not_found: "Участник не найден",
  organization_creator_cannot_leave: "Создатель не может выйти из организации или быть исключён",
  invitation_not_found: "Приглашение не найдено",
  invitation_expired: "Срок действия приглашения истёк",
  invitation_not_pending: "Приглашение уже принято или отозвано",
  invitation_email_mismatch: "Приглашение выписано на другой email",
  invitation_already_exists: "Для этого email уже есть действующее приглашение",
  member_already_exists: "Этот пользователь уже участник организации",
  role_not_found: "Роль не найдена",
  role_name_exists: "Роль с таким названием уже существует",
};

const NETWORK_MESSAGE = "Нет связи с сервером. Попробуйте позже";
const VALIDATION_MESSAGE = "Проверьте правильность введённых данных";
const DEFAULT_MESSAGE = "Что-то пошло не так. Попробуйте позже";

export class ApiError extends Error {
  readonly status: number | null;
  readonly code: string | null;

  constructor(message: string, status: number | null, code: string | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

/** Превращает ошибку клиента (тело ответа, текст или сетевую ошибку) в ApiError с понятным сообщением. */
export function toApiError(error: unknown, response: Response | undefined): ApiError {
  if (error instanceof ApiError) {
    return error;
  }
  if (!response) {
    return new ApiError(NETWORK_MESSAGE, null, null);
  }

  const body = errorBodySchema.safeParse(error);
  if (body.success) {
    const message = MESSAGES_BY_CODE[body.data.code] ?? body.data.message;
    return new ApiError(message, response.status, body.data.code);
  }
  if (response.status === 422 && validationBodySchema.safeParse(error).success) {
    return new ApiError(VALIDATION_MESSAGE, response.status, null);
  }
  return new ApiError(DEFAULT_MESSAGE, response.status, null);
}

/** Сообщение для показа пользователю из любой ошибки. */
export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  return DEFAULT_MESSAGE;
}
