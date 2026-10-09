import datetime
from typing import Any

import jwt

from src.infrastructure.auth.jwt import create_access_token
from src.settings import AuthSettings


def make_token(
    user_id: int,
    ttl: datetime.timedelta = datetime.timedelta(hours=1),
    secret_key: str | None = None,
) -> str:
    """Валидный (по умолчанию) access-токен; secret_key и ttl позволяют получить поддельный или просроченный."""
    settings = AuthSettings()  # type: ignore[call-arg]
    return create_access_token(user_id, secret_key or settings.secret_key, settings.algorithm, ttl)


def encode_raw_token(payload: dict[str, Any], algorithm: str = "HS256", secret_key: str | None = None) -> str:
    """Токен с произвольным набором claims (без exp, с нечисловым sub и т.п.)."""
    settings = AuthSettings()  # type: ignore[call-arg]
    key = None if algorithm == "none" else (secret_key or settings.secret_key)
    return jwt.encode(payload, key, algorithm=algorithm)
