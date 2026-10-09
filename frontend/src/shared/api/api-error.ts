import { z } from "zod";

const errorBodySchema = z.object({ code: z.string(), message: z.string() });
const validationBodySchema = z.object({ detail: z.array(z.unknown()) });

// Тексты для известных кодов ошибок backend (docs/usecases/auth.md)
const MESSAGES_BY_CODE: Record<string, string> = {
  user_email_exists: "Пользователь с таким email уже существует",
  invalid_credentials: "Неверный email или пароль",
  invalid_token: "Сессия истекла. Войдите снова",
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
