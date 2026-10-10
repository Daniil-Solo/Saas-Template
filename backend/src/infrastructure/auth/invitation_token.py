import hashlib
import secrets


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """SHA-256 токена в hex; в БД хранится только он."""
    return hashlib.sha256(token.encode()).hexdigest()
