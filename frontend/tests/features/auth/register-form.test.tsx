import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";

import { API } from "../../mocks/handlers";
import { server } from "../../mocks/server";
import { renderApp } from "../../utils/render-app";

async function fillForm(password: string) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("ФИО"), "Иван Петров");
  await user.type(screen.getByLabelText("Email"), "ivan@example.com");
  await user.type(screen.getByLabelText("Пароль"), password);
  await user.click(screen.getByRole("button", { name: "Зарегистрироваться" }));
}

describe("форма регистрации", () => {
  it("проверяет минимальную длину пароля", async () => {
    renderApp("/register");

    await fillForm("short");

    expect(await screen.findByText("Пароль должен быть не короче 8 символов")).toBeInTheDocument();
  });

  it("после регистрации ведёт на /login с сообщением и без сохранения токена", async () => {
    renderApp("/register");

    await fillForm("password123");

    expect(await screen.findByRole("heading", { name: "Вход" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Регистрация прошла успешно");
    expect(localStorage.getItem("access_token")).toBeNull();
  });

  it("показывает сообщение, если email уже занят", async () => {
    server.use(
      http.post(`${API}/auth/register`, () =>
        HttpResponse.json(
          { code: "user_email_exists", message: "Email already exists" },
          { status: 409 },
        ),
      ),
    );
    renderApp("/register");

    await fillForm("password123");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Пользователь с таким email уже существует",
    );
  });
});
