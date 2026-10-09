import { expect, test } from "@playwright/test";

test("регистрация, вход, сохранение сессии и выход", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;
  const password = "password123";

  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);

  await page.getByRole("link", { name: "Зарегистрироваться" }).click();
  await page.getByLabel("ФИО").fill("Тест Тестов");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Пароль").fill(password);
  await page.getByRole("button", { name: "Зарегистрироваться" }).click();

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("status")).toContainText("Регистрация прошла успешно");

  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Пароль").fill(password);
  await page.getByRole("button", { name: "Войти" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByText("Тест Тестов")).toBeVisible();
  await expect(page.getByText(email)).toBeVisible();

  await page.reload();
  await expect(page.getByText("Тест Тестов")).toBeVisible();

  await page.getByRole("button", { name: "Выйти" }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("неверный пароль показывает ошибку", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("nobody@example.com");
  await page.getByLabel("Пароль").fill("wrong-password");
  await page.getByRole("button", { name: "Войти" }).click();

  await expect(page.getByRole("alert")).toContainText("Неверный email или пароль");
});
