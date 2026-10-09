import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";

import { API, TEST_TOKEN } from "../../mocks/handlers";
import { server } from "../../mocks/server";
import { renderApp } from "../../utils/render-app";

describe("форма входа", () => {
  it("показывает ошибки валидации рядом с полями и не отправляет запрос", async () => {
    const user = userEvent.setup();
    renderApp("/login");

    await user.click(screen.getByRole("button", { name: "Войти" }));

    expect(await screen.findByText("Введите корректный email")).toBeInTheDocument();
    expect(screen.getByText("Введите пароль")).toBeInTheDocument();
  });

  it("после успешного входа сохраняет токен и открывает главную", async () => {
    const user = userEvent.setup();
    renderApp("/login");

    await user.type(screen.getByLabelText("Email"), "ivan@example.com");
    await user.type(screen.getByLabelText("Пароль"), "password123");
    await user.click(screen.getByRole("button", { name: "Войти" }));

    expect(await screen.findByText("Иван Петров")).toBeInTheDocument();
    expect(localStorage.getItem("access_token")).toBe(TEST_TOKEN);
  });

  it("показывает сообщение при неверных учётных данных", async () => {
    server.use(
      http.post(`${API}/auth/login`, () =>
        HttpResponse.json(
          { code: "invalid_credentials", message: "Invalid credentials" },
          { status: 401 },
        ),
      ),
    );
    const user = userEvent.setup();
    renderApp("/login");

    await user.type(screen.getByLabelText("Email"), "ivan@example.com");
    await user.type(screen.getByLabelText("Пароль"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Войти" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Неверный email или пароль");
    expect(localStorage.getItem("access_token")).toBeNull();
  });
});
