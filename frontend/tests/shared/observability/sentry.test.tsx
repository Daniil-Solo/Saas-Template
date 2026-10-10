import * as Sentry from "@sentry/react";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ErrorFallback } from "@/app/error-fallback";
import { createQueryClient, Providers } from "@/app/providers";
import { ApiError } from "@/shared/api";
import { config } from "@/shared/config/env";
import { beforeSend, initSentry, setSentryUser } from "@/shared/observability/sentry";

vi.mock("@sentry/react", async (importOriginal) => ({
  ...(await importOriginal<typeof Sentry>()),
  init: vi.fn(),
  setUser: vi.fn(),
}));

const configMock = vi.hoisted(() => ({ sentryDsn: null as string | null }));
vi.mock("@/shared/config/env", () => ({
  config: {
    apiUrl: "",
    get sentryDsn() {
      return configMock.sentryDsn;
    },
    sentryEnvironment: "test",
    appRelease: undefined,
  },
}));

const event: Sentry.ErrorEvent = { type: undefined };

beforeEach(() => {
  vi.clearAllMocks();
  configMock.sentryDsn = null;
});

describe("initSentry", () => {
  it("без DSN не инициализирует SDK", () => {
    initSentry();

    expect(Sentry.init).not.toHaveBeenCalled();
  });

  it("с DSN инициализирует SDK без PII и трейсинга", () => {
    configMock.sentryDsn = "https://key@sentry.example.com/1";

    initSentry();

    expect(config.sentryDsn).toBe("https://key@sentry.example.com/1");
    expect(Sentry.init).toHaveBeenCalledWith(
      expect.objectContaining({
        dsn: "https://key@sentry.example.com/1",
        environment: "test",
        dataCollection: expect.objectContaining({
          userInfo: false,
          cookies: false,
          httpBodies: [],
        }),
        tracesSampleRate: 0,
      }),
    );
  });
});

describe("setSentryUser", () => {
  it("передаёт только id", () => {
    setSentryUser(42);

    expect(Sentry.setUser).toHaveBeenCalledWith({ id: "42" });
  });

  it("null сбрасывает пользователя", () => {
    setSentryUser(null);

    expect(Sentry.setUser).toHaveBeenCalledWith(null);
  });
});

describe("beforeSend", () => {
  it("отбрасывает ожидаемые ошибки API (4xx)", () => {
    expect(beforeSend(event, { originalException: new ApiError("x", 404, null) })).toBeNull();
  });

  it("пропускает ошибки API 5xx, сетевые и прочие ошибки", () => {
    expect(beforeSend(event, { originalException: new ApiError("x", 500, null) })).toBe(event);
    expect(beforeSend(event, { originalException: new ApiError("x", null, null) })).toBe(event);
    expect(beforeSend(event, { originalException: new Error("boom") })).toBe(event);
  });
});

describe("ErrorBoundary", () => {
  it("показывает fallback с кнопкой перезагрузки при ошибке рендера", () => {
    function Broken(): never {
      throw new Error("boom");
    }
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <Providers queryClient={createQueryClient()}>
        <Broken />
      </Providers>,
    );

    consoleError.mockRestore();
    expect(screen.getByRole("alert")).toHaveTextContent("Что-то пошло не так");
    expect(screen.getByRole("button", { name: "Перезагрузить" })).toBeInTheDocument();
  });

  it("ErrorFallback рендерится отдельно", () => {
    render(<ErrorFallback />);

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
