import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";

import { API, TEST_TOKEN } from "../mocks/handlers";
import { server } from "../mocks/server";
import { renderApp } from "../utils/render-app";

describe("доступ к маршрутам", () => {
  it("неавторизованного с приватной страницы отправляет на /login", async () => {
    renderApp("/");

    expect(await screen.findByRole("heading", { name: "Вход" })).toBeInTheDocument();
  });

  it("авторизованного с /login и /register отправляет на главную", async () => {
    localStorage.setItem("access_token", TEST_TOKEN);

    renderApp("/login");

    expect(await screen.findByText("Иван Петров")).toBeInTheDocument();
  });

  it("показывает 404 для неизвестного маршрута", async () => {
    renderApp("/no-such-page");

    expect(await screen.findByRole("heading", { name: "Страница не найдена" })).toBeInTheDocument();
  });
});

describe("главная страница", () => {
  it("показывает ФИО и email текущего пользователя", async () => {
    localStorage.setItem("access_token", TEST_TOKEN);

    renderApp("/");

    expect(await screen.findByText("Иван Петров")).toBeInTheDocument();
    expect(screen.getByText("ivan@example.com")).toBeInTheDocument();
  });

  it("при ошибке загрузки показывает сообщение и кнопку повтора", async () => {
    localStorage.setItem("access_token", TEST_TOKEN);
    server.use(http.get(`${API}/users/me`, () => HttpResponse.error()));

    renderApp("/");

    expect(await screen.findByRole("alert")).toHaveTextContent("Нет связи с сервером");
    expect(screen.getByRole("button", { name: "Повторить" })).toBeInTheDocument();
  });

  it("при 401 сбрасывает сессию и ведёт на /login", async () => {
    localStorage.setItem("access_token", "expired-token");

    renderApp("/");

    expect(await screen.findByRole("heading", { name: "Вход" })).toBeInTheDocument();
    expect(localStorage.getItem("access_token")).toBeNull();
  });

  it("кнопка «Выйти» удаляет токен и ведёт на /login", async () => {
    localStorage.setItem("access_token", TEST_TOKEN);
    const user = userEvent.setup();
    renderApp("/");

    await user.click(await screen.findByRole("button", { name: "Выйти" }));

    expect(await screen.findByRole("heading", { name: "Вход" })).toBeInTheDocument();
    expect(localStorage.getItem("access_token")).toBeNull();
  });
});
