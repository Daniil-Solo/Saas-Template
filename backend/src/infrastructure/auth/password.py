import asyncio

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
# Хеш-заглушка: при логине несуществующего пользователя тратим то же время на проверку пароля
_DUMMY_HASH = _hasher.hash("dummy-password")


def _verify(password: str, hashed_password: str) -> bool:
    try:
        return _hasher.verify(hashed_password, password)
    except (VerificationError, InvalidHashError):
        return False


async def hash_password(password: str) -> str:
    # argon2 нагружает CPU, поэтому выносим в поток, чтобы не блокировать event loop
    return await asyncio.to_thread(_hasher.hash, password)


async def verify_password(password: str, hashed_password: str) -> bool:
    return await asyncio.to_thread(_verify, password, hashed_password)


async def verify_dummy_password(password: str) -> None:
    await asyncio.to_thread(_verify, password, _DUMMY_HASH)


def needs_rehash(hashed_password: str) -> bool:
    return _hasher.check_needs_rehash(hashed_password)
