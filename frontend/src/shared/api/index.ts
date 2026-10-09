import { toApiError } from "./api-error";
import { getApiToken, handleUnauthorized } from "./auth-handlers";
import { client } from "./generated/client.gen";

// Единое место обработки ошибок: ApiError с сообщением для пользователя и сброс сессии при 401
client.interceptors.response.use((response) => {
  if (response.status === 401 && getApiToken() !== null) {
    handleUnauthorized();
  }
  return response;
});
client.interceptors.error.use((error, response) => toApiError(error, response));

export { ApiError, getErrorMessage } from "./api-error";
export { configureApiAuth } from "./auth-handlers";
