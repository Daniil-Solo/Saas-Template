import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { buildAuthPath, sanitizeNext } from "@/features/auth/next-path";

import { TEST_TOKEN } from "../../mocks/handlers";
import { renderApp } from "../../utils/render-app";

describe("sanitizeNext", () => {
  it("пропускает только пути внутри приложения", () => {
    expect(sanitizeNext("/invitations/abc")).toBe("/invitations/abc");
    expect(sanitizeNext("https://evil.example")).toBeNull();
    expect(sanitizeNext("//evil.example")).toBeNull();
    expect(sanitizeNext("/\\evil.example")).toBeNull();
    expect(sanitizeNext(null)).toBeNull();
  });
});

describe("buildAuthPath", () => {
  it("добавляет next, кроме главной страницы", () => {
    expect(buildAuthPath("/login", "/invitations/abc")).toBe("/login?next=%2Finvitations%2Fabc");
    expect(buildAuthPath("/login", "/")).toBe("/login");
    expect(buildAuthPath("/register", null)).toBe("/register");
  });
});

describe("возврат после входа", () => {
  it("приватный маршрут сохраняет путь в next", async () => {
    const router = renderApp("/invitations/abc");

    expect(await screen.findByRole("heading", { name: "Вход" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
    expect(router.state.location.search).toBe("?next=%2Finvitations%2Fabc");
  });

  it("после входа возвращает на исходный путь", async () => {
    const user = userEvent.setup();
    const router = renderApp("/login?next=%2Finvitations%2Fabc");

    await user.type(screen.getByLabelText("Email"), "ivan@example.com");
    await user.type(screen.getByLabelText("Пароль"), "password123");
    await user.click(screen.getByRole("button", { name: "Войти" }));

    await screen.findByRole("heading", { name: "Приглашение в организацию" });
    expect(router.state.location.pathname).toBe("/invitations/abc");
    expect(localStorage.getItem("access_token")).toBe(TEST_TOKEN);
  });

  it("внешний next игнорируется", async () => {
    localStorage.setItem("access_token", TEST_TOKEN);
    const router = renderApp("/login?next=https%3A%2F%2Fevil.example");

    expect(await screen.findByText("Иван Петров")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/");
  });

  it("ссылки между входом и регистрацией сохраняют next", async () => {
    renderApp("/login?next=%2Finvitations%2Fabc");

    const link = await screen.findByRole("link", { name: "Зарегистрироваться" });
    expect(link).toHaveAttribute("href", "/register?next=%2Finvitations%2Fabc");
  });
});
