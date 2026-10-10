import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import {
  makeInvitation,
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

function organizationHandlers(overrides: Parameters<typeof makeOrganizationDetail>[0] = {}) {
  server.use(
    http.get(`${API}/organizations/1`, () => HttpResponse.json(makeOrganizationDetail(overrides))),
  );
}

describe("страница приглашений организации", () => {
  it("без права показывает «нет доступа»", async () => {
    login();
    organizationHandlers({ permissions: [], is_creator: false });
    renderApp("/organizations/1/invitations");

    expect(await screen.findByRole("alert")).toHaveTextContent("Нет доступа");
  });

  it("показывает пустое состояние", async () => {
    login();
    organizationHandlers();
    server.use(http.get(`${API}/organizations/1/invitations`, () => HttpResponse.json([])));
    renderApp("/organizations/1/invitations");

    expect(await screen.findByText("Приглашений пока нет.")).toBeInTheDocument();
  });

  it("показывает приглашения со статусами и отзывает действующее", async () => {
    login();
    organizationHandlers();
    let revoked = false;
    server.use(
      http.get(`${API}/organizations/1/invitations`, () =>
        HttpResponse.json([
          makeInvitation(),
          makeInvitation({ id: 2, email: "old@example.com", status: "expired" }),
        ]),
      ),
      http.delete(`${API}/organizations/1/invitations/1`, () => {
        revoked = true;
        return HttpResponse.json({ message: "ok" });
      }),
    );
    const user = userEvent.setup();
    renderApp("/organizations/1/invitations");

    expect(await screen.findByText("Действует")).toBeInTheDocument();
    expect(screen.getByText("Истекло")).toBeInTheDocument();
    // отозвать можно только действующее
    expect(screen.getAllByRole("button", { name: /Отозвать/ })).toHaveLength(1);

    await user.click(
      screen.getByRole("button", { name: "Отозвать приглашение для anna@example.com" }),
    );

    await vi.waitFor(() => expect(revoked).toBe(true));
  });

  it("создаёт приглашение и показывает ссылку", async () => {
    login();
    organizationHandlers();
    let sentBody: unknown;
    server.use(
      http.get(`${API}/roles`, () => HttpResponse.json([makeRole()])),
      http.get(`${API}/organizations/1/invitations`, () => HttpResponse.json([])),
      http.post(`${API}/organizations/1/invitations`, async ({ request }) => {
        sentBody = await request.json();
        return HttpResponse.json({ ...makeInvitation(), token: "secret-token" }, { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderApp("/organizations/1/invitations");

    await user.type(await screen.findByLabelText("Email приглашаемого"), "anna@example.com");
    await user.click(await screen.findByLabelText("Менеджер"));
    await user.click(screen.getByRole("button", { name: "Создать приглашение" }));

    const link = await screen.findByLabelText("Ссылка-приглашение");
    expect(link).toHaveValue(`${window.location.origin}/invitations/secret-token`);
    expect(sentBody).toEqual({ email: "anna@example.com", role_ids: [1] });
  });

  it("валидирует email и показывает ошибку backend", async () => {
    login();
    organizationHandlers();
    server.use(
      http.get(`${API}/organizations/1/invitations`, () => HttpResponse.json([])),
      http.post(`${API}/organizations/1/invitations`, () =>
        HttpResponse.json(
          { code: "invitation_already_exists", message: "exists" },
          { status: 409 },
        ),
      ),
    );
    const user = userEvent.setup();
    renderApp("/organizations/1/invitations");

    await user.click(await screen.findByRole("button", { name: "Создать приглашение" }));
    expect(await screen.findByText("Введите корректный email")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Email приглашаемого"), "anna@example.com");
    await user.click(screen.getByRole("button", { name: "Создать приглашение" }));
    expect(
      await screen.findByText("Для этого email уже есть действующее приглашение"),
    ).toBeInTheDocument();
  });
});

describe("принятие приглашения", () => {
  const preview = {
    organization_id: 1,
    organization_name: "Acme",
    email: "ivan@example.com",
    status: "active",
    roles: [makeRole()],
    expires_at: "2026-12-31T00:00:00Z",
  };

  it("неавторизованного отправляет на вход с возвратом", async () => {
    const router = renderApp("/invitations/abc");

    expect(await screen.findByRole("heading", { name: "Вход" })).toBeInTheDocument();
    expect(router.state.location.search).toBe("?next=%2Finvitations%2Fabc");
  });

  it("показывает организацию и роли и принимает приглашение", async () => {
    login();
    server.use(
      http.get(`${API}/invitations/abc`, () => HttpResponse.json(preview)),
      http.post(`${API}/invitations/abc/accept`, () => HttpResponse.json(makeOrganization())),
      organizationDetailHandler(),
      http.get(`${API}/organizations/1/members`, () => HttpResponse.json([makeMember()])),
    );
    const user = userEvent.setup();
    const router = renderApp("/invitations/abc");

    expect(await screen.findByText("Acme")).toBeInTheDocument();
    expect(screen.getByText("Менеджер")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Принять приглашение" }));

    await screen.findByRole("heading", { name: "Участники" });
    expect(router.state.location.pathname).toBe("/organizations/1/members");
  });

  it("показывает ошибку, если email не совпадает", async () => {
    login();
    server.use(
      http.get(`${API}/invitations/abc`, () => HttpResponse.json(preview)),
      http.post(`${API}/invitations/abc/accept`, () =>
        HttpResponse.json(
          { code: "invitation_email_mismatch", message: "mismatch" },
          { status: 403 },
        ),
      ),
    );
    const user = userEvent.setup();
    renderApp("/invitations/abc");

    await user.click(await screen.findByRole("button", { name: "Принять приглашение" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Приглашение выписано на другой email",
    );
  });

  it("для истёкшего приглашения нет кнопки принятия", async () => {
    login();
    server.use(
      http.get(`${API}/invitations/abc`, () =>
        HttpResponse.json({ ...preview, status: "expired" }),
      ),
    );
    renderApp("/invitations/abc");

    expect(await screen.findByText(/Срок действия приглашения истёк/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Принять приглашение" })).not.toBeInTheDocument();
  });

  it("для неизвестного приглашения показывает ошибку", async () => {
    login();
    server.use(
      http.get(`${API}/invitations/abc`, () =>
        HttpResponse.json({ code: "invitation_not_found", message: "nf" }, { status: 404 }),
      ),
    );
    renderApp("/invitations/abc");

    expect(await screen.findByRole("alert")).toHaveTextContent("Приглашение не найдено");
  });
});

function organizationDetailHandler() {
  return http.get(`${API}/organizations/1`, () => HttpResponse.json(makeOrganizationDetail()));
}
