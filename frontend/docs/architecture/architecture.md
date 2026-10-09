## Архитектура фронтенда

Диаграммы - источник истины по составу клиента и отправная точка разработки. Новая внешняя интеграция или принципиально новый слой сначала добавляется на диаграммы, и только потом реализуется в коде. Общая системная архитектура (backend, БД, воркер) описана в `backend/docs/architecture/architecture.md`.

### Контекст

```mermaid
flowchart LR
    user("Пользователь")

    subgraph Client["Веб-клиент (SPA)"]
        ui("UI: страницы и компоненты")
        state("Серверное состояние: TanStack Query")
        apiClient("API-клиент: сгенерирован из OpenAPI")
    end

    api("Backend API")

    user --> ui
    ui --> state
    state --> apiClient
    apiClient -->|"HTTP/JSON, /api/v1/*"| api
```

### Слои

Зависимости направлены только вниз.

```mermaid
flowchart TD
    app("app: провайдеры, роутер, глобальные стили")
    pages("pages: страницы-маршруты")
    features("features: пользовательские сценарии (формы, действия)")
    shared("shared: api, ui, lib, config")

    app --> pages
    pages --> features
    pages --> shared
    features --> shared
```

### Поток данных

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant P as Page / Feature
    participant Q as TanStack Query
    participant C as API-клиент
    participant B as Backend

    U->>P: действие
    P->>Q: useQuery / useMutation
    Q->>C: вызов сгенерированной функции
    C->>B: HTTP-запрос (Bearer-токен)
    B-->>C: JSON / ошибка
    C-->>Q: типизированный ответ / ApiError
    Q-->>P: data, isPending, error
    P-->>U: UI-состояние
```
