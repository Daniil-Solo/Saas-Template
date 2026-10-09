import { ApiError, toApiError } from "@/shared/api/api-error";

const response = (status: number) => new Response(null, { status });

describe("toApiError", () => {
  it("сопоставляет известный код ошибки с русским сообщением", () => {
    const error = toApiError({ code: "invalid_token", message: "x" }, response(401));

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(401);
    expect(error.code).toBe("invalid_token");
    expect(error.message).toBe("Сессия истекла. Войдите снова");
  });

  it("для неизвестного кода использует message из ответа", () => {
    const error = toApiError({ code: "something", message: "Описание" }, response(400));

    expect(error.message).toBe("Описание");
  });

  it("для ошибки валидации 422 возвращает общее сообщение", () => {
    const error = toApiError({ detail: [{ msg: "x" }] }, response(422));

    expect(error.message).toBe("Проверьте правильность введённых данных");
  });

  it("при отсутствии ответа считает ошибку сетевой", () => {
    const error = toApiError(new TypeError("Failed to fetch"), undefined);

    expect(error.status).toBeNull();
    expect(error.message).toBe("Нет связи с сервером. Попробуйте позже");
  });
});
