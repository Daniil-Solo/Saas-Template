## Модель данных

Эта диаграмма - источник истины по модели данных и отправная точка разработки. Сначала меняется диаграмма (новые сущности, поля, связи, enum), затем по ней пишутся SQLAlchemy-модели, DTO, DAO и миграции. Код должен точно соответствовать диаграмме.

В шаблоне есть пользователи (`users`) и блок организаций: организации, участники, роли, права ролей, приглашения.

```mermaid
erDiagram
    users {
        integer id PK
        string fullname
        string email UK
        string hashed_password
        bool is_verified
        bool is_admin
        datetime created_at
    }

    organizations {
        integer id PK
        string name
        integer created_by_id FK
        datetime created_at
    }

    organization_members {
        integer id PK
        integer organization_id FK
        integer user_id FK
        datetime created_at
    }

    roles {
        integer id PK
        string name UK
        datetime created_at
    }

    role_permissions {
        integer role_id PK, FK
        string permission PK
    }

    member_roles {
        integer member_id PK, FK
        integer role_id PK, FK
    }

    invitations {
        integer id PK
        integer organization_id FK
        string email
        string token_hash UK
        enum status
        datetime expires_at
        integer invited_by_id FK
        datetime created_at
        datetime accepted_at
    }

    invitation_roles {
        integer invitation_id PK, FK
        integer role_id PK, FK
    }

    users ||--o{ organizations : "создаёт (created_by_id)"
    users ||--o{ organization_members : "состоит"
    organizations ||--o{ organization_members : "включает"
    organization_members ||--o{ member_roles : "имеет"
    roles ||--o{ member_roles : "назначена"
    roles ||--o{ role_permissions : "даёт"
    organizations ||--o{ invitations : "выдаёт"
    users ||--o{ invitations : "приглашает (invited_by_id)"
    invitations ||--o{ invitation_roles : "включает"
    roles ||--o{ invitation_roles : "назначается"
```

Примечания к `users`:
- `email` уникален.
- `is_verified` при создании пользователя равен `true`. Это упрощение шаблона: в реальном проекте здесь должна быть верификация email (письмо со ссылкой), а `is_verified` должен создаваться как `false`.
- `is_admin` по умолчанию `false`, `created_at` заполняется на стороне БД (`now()`). `is_admin` даёт право создавать роли и менять их права; первого администратора назначают вручную в БД.

Примечания к организациям и участникам:
- `organizations.created_by_id` - создатель; в своей организации он проходит любую проверку права без ролей, его нельзя исключить и он не может выйти. Удаление пользователя, создавшего организацию, запрещено (`RESTRICT`).
- При создании организации создателю сразу добавляется запись в `organization_members` (без ролей).
- Пара (`organization_id`, `user_id`) в `organization_members` уникальна. Внешние ключи на организацию и пользователя - `CASCADE`.

Примечания к ролям и правам:
- Роли глобальные (не привязаны к организации); создаёт и меняет их только администратор системы. `name` уникально.
- Права - константы в коде (`Permission`: `members:manage`, `invitations:manage`). В БД хранится только привязка роли к коду права (`role_permissions.permission`); допустимость кода проверяется на уровне приложения, отдельной таблицы справочника нет.
- Эффективные права участника - объединение прав всех его ролей (`member_roles`).
- Внешние ключи на `roles` в `role_permissions`, `member_roles`, `invitation_roles` - `CASCADE`: удаление роли снимает её у участников и из приглашений.

Примечания к приглашениям:
- `status` - enum `pending` / `accepted` / `revoked`. Состояние «истекло» не хранится: это `pending` с `expires_at` в прошлом.
- В БД лежит только хеш токена (`token_hash`, SHA-256); сам токен возвращается один раз при создании.
- Частичный уникальный индекс по (`organization_id`, `email`) при `status = 'pending'`: на email в организации одно действующее приглашение. Просроченные `pending` переводятся в `revoked` при создании нового приглашения на тот же email.
- `accepted_at` заполняется при принятии. Внешние ключи на организацию - `CASCADE`, `invited_by_id` - `SET NULL`.
