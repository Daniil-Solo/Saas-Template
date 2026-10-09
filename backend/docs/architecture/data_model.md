## Модель данных

Эта диаграмма - источник истины по модели данных и отправная точка разработки. Сначала меняется диаграмма (новые сущности, поля, связи, enum), затем по ней пишутся SQLAlchemy-модели, DTO, DAO и миграции. Код должен точно соответствовать диаграмме.

В шаблоне есть одна таблица - `users`.

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
```

Примечания к `users`:
- `email` уникален.
- `is_verified` при создании пользователя равен `true`. Это упрощение шаблона: в реальном проекте здесь должна быть верификация email (письмо со ссылкой), а `is_verified` должен создаваться как `false`.
- `is_admin` по умолчанию `false`, `created_at` заполняется на стороне БД (`now()`).
