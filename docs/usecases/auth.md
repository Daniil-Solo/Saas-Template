# Аутентификация и профиль пользователя

## Цель
Дать пользователю возможность зарегистрироваться, войти по email и паролю и получить информацию о себе по JWT-токену.

## Пользовательский сценарий
1. Новый пользователь отправляет ФИО, email и пароль на регистрацию и сразу получает access-токен.
2. Существующий пользователь отправляет email и пароль на логин и получает access-токен.
3. Клиент передаёт токен в заголовке `Authorization: Bearer <token>` и получает данные текущего пользователя.

## Предложение по реализации

### Backend
- Сущность: `users` (см. `backend/docs/architecture/data_model.md`): `id`, `fullname`, `email` (уникальный), `hashed_password`, `is_verified`, `is_admin`, `created_at`.
- Эндпоинты:

| Метод | Путь | Доступ | Вход | Ответ |
|-------|------|--------|------|-------|
| POST | `/api/v1/auth/register` | публичный | `UserRegisterDTO` (fullname, email, password) | `TokenDTO` |
| POST | `/api/v1/auth/login` | публичный | `UserLoginDTO` (email, password) | `TokenDTO` |
| GET | `/api/v1/users/me` | JWT | заголовок `Authorization: Bearer` | `UserDTO` |

- Email приводится к нижнему регистру и обрезается по краям в DTO (при регистрации и логине); в БД уникален.
- Пароль при регистрации: от 8 до 128 символов, без требований к составу.
- Токен: один access JWT (HS256, секрет `AUTH_SECRET_KEY`), `sub` = id пользователя, `exp` обязателен; срок жизни задаётся переменной окружения `AUTH_ACCESS_TOKEN_TTL_MINUTES` (по умолчанию 60 минут). Refresh-токенов нет.
- Пароли хешируются argon2 (`argon2-cffi`).
- При регистрации `is_verified=true` (упрощение шаблона; в коде оставляем комментарий, что в реальном проекте нужна верификация email и значение `false`). Подтверждение email вне рамок.
- Ошибки (код в `code`, HTTP-статус задаётся в `error_status_mapping.py`):

| Ситуация | HTTP | code |
|----------|------|------|
| Email уже занят | 409 | `user_email_exists` |
| Неверный email или пароль | 401 | `invalid_credentials` |
| Токен отсутствует, просрочен или некорректен | 401 | `invalid_token` |
| Пользователь из токена не найден | 401 | `invalid_token` |
| Ошибка валидации входа | 422 | стандартный FastAPI |

Диаграмма последовательности:

```mermaid
sequenceDiagram
    actor U as Клиент
    participant API as API (router)
    participant S as Сервис (application)
    participant DAO as DAO (UnitOfWork)
    participant DB as PostgreSQL

    rect rgb(240, 245, 255)
    note over U,DB: Регистрация
    U->>API: POST /api/v1/auth/register (fullname, email, password)
    API->>S: auth.register(data)
    S->>S: хеш пароля (argon2); email уже нормализован в DTO
    S->>DAO: users.create(...)
    DAO->>DB: INSERT users
    alt email уже занят
        DB-->>DAO: нарушение уникальности
        S-->>API: UserEmailExistsError
        API-->>U: 409 user_email_exists
    else успех
        S->>S: создать JWT (sub = id)
        S-->>API: TokenDTO
        API-->>U: 200 TokenDTO
    end
    end

    rect rgb(240, 255, 245)
    note over U,DB: Логин
    U->>API: POST /api/v1/auth/login (email, password)
    API->>S: auth.login(data)
    S->>DAO: users.get_by_email(email)
    DAO->>DB: SELECT users
    alt нет пользователя или пароль не совпал
        S-->>API: InvalidCredentialsError
        API-->>U: 401 invalid_credentials
    else успех
        S-->>API: TokenDTO
        API-->>U: 200 TokenDTO
    end
    end

    rect rgb(255, 250, 240)
    note over U,DB: Текущий пользователь
    U->>API: GET /api/v1/users/me (Authorization: Bearer)
    API->>API: get_current_user: декодировать JWT
    API->>S: users.get_by_id(sub)
    S->>DAO: users.get_by_id(id)
    DAO->>DB: SELECT users
    alt токен некорректен или пользователь не найден
        API-->>U: 401 invalid_token
    else успех
        API-->>U: 200 UserDTO
    end
    end
```

### Frontend
Вне рамок этой задачи. После готовности backend клиент генерируется командой `pnpm gen:api`.

## Вне рамок
- Refresh-токены, выход с отзывом токена.
- Подтверждение email, восстановление пароля.
- Rate limiting на логин.
- Роли и права (поле `is_admin` есть в модели, но не используется).
- Frontend-страницы входа и регистрации.
