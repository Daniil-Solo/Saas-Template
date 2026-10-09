import datetime

import jwt


class TokenDecodeError(Exception):
    """Токен некорректен, просрочен или не содержит обязательных claims."""


def create_access_token(user_id: int, secret_key: str, algorithm: str, ttl: datetime.timedelta) -> str:
    now = datetime.datetime.now(datetime.UTC)
    payload = {"sub": str(user_id), "iat": now, "exp": now + ttl}
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(token: str, secret_key: str, algorithm: str) -> int:
    try:
        # algorithms задаем явно из настроек: токены с другим алгоритмом (в том числе alg=none) отклоняются
        payload = jwt.decode(token, secret_key, algorithms=[algorithm], options={"require": ["exp", "sub"]})
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise TokenDecodeError from exc
