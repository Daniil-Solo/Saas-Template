import { HttpResponse, http } from "msw";

import { makeUser } from "./factories";

export const API = "http://localhost/api/v1";
export const TEST_TOKEN = "test-token";

export const handlers = [
  http.post(`${API}/auth/login`, () =>
    HttpResponse.json({ access_token: TEST_TOKEN, token_type: "bearer" }),
  ),
  http.post(`${API}/auth/register`, () =>
    HttpResponse.json({ access_token: TEST_TOKEN, token_type: "bearer" }),
  ),
  http.get(`${API}/users/me`, ({ request }) => {
    if (request.headers.get("Authorization") !== `Bearer ${TEST_TOKEN}`) {
      return HttpResponse.json(
        { code: "invalid_token", message: "Токен некорректен" },
        { status: 401 },
      );
    }
    return HttpResponse.json(makeUser());
  }),
];
