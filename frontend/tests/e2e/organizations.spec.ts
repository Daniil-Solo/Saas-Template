import { expect, type Page, test } from "@playwright/test";

const PASSWORD = "password123";

async function register(page: Page, fullname: string, email: string) {
  await page.getByLabel("ФИО").fill(fullname);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Пароль").fill(PASSWORD);
  await page.getByRole("button", { name: "Зарегистрироваться" }).click();
}

async function login(page: Page, email: string) {
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Пароль").fill(PASSWORD);
  await page.getByRole("button", { name: "Войти" }).click();
}

test("создать организацию, пригласить коллегу и принять приглашение", async ({ browser }) => {
  const stamp = Date.now();
  const ownerEmail = `owner-${stamp}@example.com`;
  const guestEmail = `guest-${stamp}@example.com`;
  const orgName = `Acme ${stamp}`;

  // Создатель: регистрация, вход, организация, приглашение
  const ownerContext = await browser.newContext();
  const owner = await ownerContext.newPage();
  await owner.goto("/register");
  await register(owner, "Владелец Тестов", ownerEmail);
  await expect(owner).toHaveURL(/\/login$/);
  await login(owner, ownerEmail);

  await expect(owner.getByText("У вас пока нет организаций")).toBeVisible();
  await owner.getByRole("link", { name: "Создать организацию" }).click();
  await owner.getByLabel("Название").fill(orgName);
  await owner.getByRole("button", { name: "Создать организацию" }).click();

  await expect(owner.getByRole("heading", { name: orgName })).toBeVisible();
  await expect(owner.getByText("Создатель")).toBeVisible();

  await owner.getByRole("link", { name: "Приглашения" }).click();
  await owner.getByLabel("Email приглашаемого").fill(guestEmail);
  await owner.getByRole("button", { name: "Создать приглашение" }).click();
  const link = await owner.getByLabel("Ссылка-приглашение").inputValue();
  expect(link).toContain("/invitations/");
  await expect(owner.getByRole("cell", { name: guestEmail, exact: true })).toBeVisible();
  await ownerContext.close();

  // Приглашённый: ссылка → регистрация → вход → принятие
  const guestContext = await browser.newContext();
  const guest = await guestContext.newPage();
  await guest.goto(new URL(link).pathname);
  await expect(guest).toHaveURL(/\/login\?next=/);

  await guest.getByRole("link", { name: "Зарегистрироваться" }).click();
  await register(guest, "Гость Тестов", guestEmail);
  await expect(guest).toHaveURL(/\/login\?next=/);
  await login(guest, guestEmail);

  await expect(guest.getByRole("heading", { name: "Приглашение в организацию" })).toBeVisible();
  await expect(guest.getByText(orgName)).toBeVisible();
  await guest.getByRole("button", { name: "Принять приглашение" }).click();

  await expect(guest.getByRole("heading", { name: orgName })).toBeVisible();
  await expect(guest.getByText("Владелец Тестов")).toBeVisible();
  await expect(guest.getByText("Гость Тестов (вы)")).toBeVisible();
  await expect(guest.getByRole("button", { name: "Выйти из организации" })).toBeVisible();
  await guestContext.close();
});
