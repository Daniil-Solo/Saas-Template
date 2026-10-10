import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import {
  makeMember,
  makeOrganization,
  makeOrganizationDetail,
  makeRole,
} from "../../mocks/factories";
import { API, TEST_TOKEN } from "../../mocks/handlers";
import { server } from "../../mocks/server";
import { renderApp } from "../../utils/render-app";

function login() {
  localStorage.setItem("access_token", TEST_TOKEN);
}

describe("мои организации", () => {
  it("показывает пустое состояние", async () => {
    login();
    renderApp("/");

    expect(await screen.findByText(/У вас пока нет организаций/)).toBeInTheDocument();
  });

  it("показывает список организаций со ссылками", async () => {
    login();
    server.use(
      http.get(`${API}/organizations`, () =>
        HttpResponse.json([makeOrganization(), makeOrganization({ id: 2, name: "Globex" })]),
      ),
    );
    renderApp("/");

    const link = await screen.findByRole("link", { name: "Globex" });
    expect(link).toHaveAttribute("href", "/organizations/2/members");
  });

  it("при ошибке показывает сообщение и кнопку повтора", async () => {
    login();
    server.use(http.get(`${API}/organizations`, () => HttpResponse.error()));
    renderApp("/");

    expect(await screen.findAllByRole("alert")).not.toHaveLength(0);
    expect(screen.getByRole("button", { name: "Повторить" })).toBeInTheDocument();
  });

  it("переключатель открывает выбранную организацию и запоминает её", async () => {
    login();
    server.use(
      http.get(`${API}/organizations`, () =>
        HttpResponse.json([makeOrganization(), makeOrganization({ id: 2, name: "Globex" })]),
      ),
      http.get(`${API}/organizations/2`, () =>
        HttpResponse.json(makeOrganizationDetail({ id: 2, name: "Globex" })),
      ),
      http.get(`${API}/organizations/2/members`, () => HttpResponse.json([makeMember()])),
    );
    const user = userEvent.setup();
    const router = renderApp("/");

    const select = await screen.findByRole("combobox", { name: "Организация" });
    await screen.findByRole("option", { name: "Globex" });
    await user.selectOptions(select, "Globex");

    expect(await screen.findByRole("heading", { name: "Globex" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/organizations/2/members");
    expect(localStorage.getItem("last_organization_id")).toBe("2");
  });
});

describe("создание организации", () => {
  it("валидирует название", async () => {
    login();
    const user = userEvent.setup();
    renderApp("/organizations/new");

    await user.click(await screen.findByRole("button", { name: "Создать организацию" }));

    expect(await screen.findByText("Введите название")).toBeInTheDocument();
  });

  it("создаёт организацию и открывает список участников", async () => {
    login();
    let sentName: unknown;
    server.use(
      http.post(`${API}/organizations`, async ({ request }) => {
        const body = (await request.json()) as { name: string };
        sentName = body.name;
        return HttpResponse.json(makeOrganization({ id: 5, name: body.name }), { status: 201 });
      }),
      http.get(`${API}/organizations/5`, () =>
        HttpResponse.json(makeOrganizationDetail({ id: 5, name: "Новая" })),
      ),
      http.get(`${API}/organizations/5/members`, () => HttpResponse.json([makeMember()])),
    );
    const user = userEvent.setup();
    renderApp("/organizations/new");

    await user.type(await screen.findByLabelText("Название"), "Новая");
    await user.click(screen.getByRole("button", { name: "Создать организацию" }));

    expect(await screen.findByRole("heading", { name: "Новая" })).toBeInTheDocument();
    expect(sentName).toBe("Новая");
    expect(localStorage.getItem("last_organization_id")).toBe("5");
  });

  it("показывает ошибку backend", async () => {
    login();
    server.use(
      http.post(`${API}/organizations`, () =>
        HttpResponse.json({ code: "permission_denied", message: "denied" }, { status: 403 }),
      ),
    );
    const user = userEvent.setup();
    renderApp("/organizations/new");

    await user.type(await screen.findByLabelText("Название"), "Новая");
    await user.click(screen.getByRole("button", { name: "Создать организацию" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Недостаточно прав");
  });
});

describe("участники", () => {
  const ivan = makeMember();
  const anna = makeMember({
    id: 2,
    user: { id: 2, fullname: "Анна Смирнова", email: "anna@example.com" },
    roles: [makeRole()],
    is_creator: false,
  });

  function useOrganizationData(overrides: Parameters<typeof makeOrganizationDetail>[0] = {}) {
    server.use(
      http.get(`${API}/organizations/1`, () =>
        HttpResponse.json(makeOrganizationDetail(overrides)),
      ),
      http.get(`${API}/organizations/1/members`, () => HttpResponse.json([ivan, anna])),
      http.get(`${API}/roles`, () =>
        HttpResponse.json([makeRole(), makeRole({ id: 2, name: "Наблюдатель", permissions: [] })]),
      ),
    );
  }

  it("создателю показывает действия над другими участниками", async () => {
    login();
    useOrganizationData();
    renderApp("/organizations/1/members");

    expect(await screen.findByText("Анна Смирнова")).toBeInTheDocument();
    expect(screen.getByText("Создатель")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Изменить роли" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Исключить" })).toBeInTheDocument();
    // создатель не может выйти
    expect(screen.queryByRole("button", { name: "Выйти из организации" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Приглашения" })).toBeInTheDocument();
  });

  it("обычному участнику скрывает действия и меню приглашений", async () => {
    login();
    useOrganizationData({ permissions: [], is_creator: false });
    renderApp("/organizations/1/members");

    expect(await screen.findByText("Анна Смирнова")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Изменить роли" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Исключить" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Приглашения" })).not.toBeInTheDocument();
  });

  it("меняет роли участника", async () => {
    login();
    useOrganizationData();
    let sentRoleIds: unknown;
    server.use(
      http.put(`${API}/organizations/1/members/2/roles`, async ({ request }) => {
        const body = (await request.json()) as { role_ids: number[] };
        sentRoleIds = body.role_ids;
        return HttpResponse.json({ ...anna, roles: [makeRole({ id: 2, name: "Наблюдатель" })] });
      }),
    );
    const user = userEvent.setup();
    renderApp("/organizations/1/members");

    await user.click(await screen.findByRole("button", { name: "Изменить роли" }));
    await user.click(await screen.findByLabelText("Менеджер"));
    await user.click(screen.getByLabelText("Наблюдатель"));
    await user.click(screen.getByRole("button", { name: "Сохранить" }));

    expect(await screen.findByRole("button", { name: "Изменить роли" })).toBeInTheDocument();
    expect(sentRoleIds).toEqual([2]);
  });

  it("исключает участника", async () => {
    login();
    useOrganizationData();
    let removed = false;
    server.use(
      http.delete(`${API}/organizations/1/members/2`, () => {
        removed = true;
        return HttpResponse.json({ message: "ok" });
      }),
    );
    const user = userEvent.setup();
    renderApp("/organizations/1/members");

    await user.click(await screen.findByRole("button", { name: "Исключить" }));

    await vi.waitFor(() => expect(removed).toBe(true));
  });

  it("участник может выйти из организации", async () => {
    login();
    server.use(
      http.get(`${API}/organizations/1`, () =>
        HttpResponse.json(makeOrganizationDetail({ permissions: [], is_creator: false })),
      ),
      http.get(`${API}/organizations/1/members`, () =>
        HttpResponse.json([
          ivan,
          makeMember({
            id: 3,
            user: { id: 1, fullname: "Иван Петров", email: "ivan@example.com" },
            is_creator: false,
          }),
        ]),
      ),
      http.delete(`${API}/organizations/1/members/3`, () => HttpResponse.json({ message: "ok" })),
    );
    localStorage.setItem("last_organization_id", "1");
    const user = userEvent.setup();
    const router = renderApp("/organizations/1/members");

    await user.click(await screen.findByRole("button", { name: "Выйти из организации" }));

    await screen.findByRole("heading", { name: "Профиль" });
    expect(router.state.location.pathname).toBe("/");
    expect(localStorage.getItem("last_organization_id")).toBeNull();
  });

  it("показывает «организация не найдена» для чужой организации", async () => {
    login();
    server.use(
      http.get(`${API}/organizations/9`, () =>
        HttpResponse.json(
          { code: "organization_not_found", message: "not found" },
          { status: 404 },
        ),
      ),
    );
    renderApp("/organizations/9/members");

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("Организация не найдена")).toBeInTheDocument();
  });

  it("показывает пустое состояние и ошибку списка участников", async () => {
    login();
    server.use(
      http.get(`${API}/organizations/1`, () => HttpResponse.json(makeOrganizationDetail())),
      http.get(`${API}/organizations/1/members`, () => HttpResponse.json([])),
    );
    renderApp("/organizations/1/members");

    expect(await screen.findByText("В организации пока нет участников.")).toBeInTheDocument();
  });
});
