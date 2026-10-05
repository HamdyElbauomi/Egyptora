"""Password hashing and JWT tokens.

Owner: Person 1.
"""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def _token(user_id: int, role: str, kind: str, lifetime: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "role": role, "type": kind, "iat": now, "exp": now + lifetime}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, role: str) -> str:
    return _token(user_id, role, "access", timedelta(minutes=settings.access_token_minutes))


def create_refresh_token(user_id: int, role: str) -> str:
    return _token(user_id, role, "refresh", timedelta(days=settings.refresh_token_days))


def decode_token(token: str, expected_type: str) -> dict:
    """Raises jwt.PyJWTError if the token is invalid, expired or of the wrong type."""
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("wrong token type")
    return payload
