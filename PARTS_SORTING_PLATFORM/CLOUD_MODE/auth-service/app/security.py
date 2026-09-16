"""Password hashing and JWT issuance/verification (RS256)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt
from passlib.context import CryptContext

from app.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def _create_token(subject: str, kind: Literal["access", "refresh"], expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": kind,
        "iss": settings.jwt_issuer,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_private_key, algorithm="RS256")


def create_access_token(user_id: str) -> str:
    return _create_token(user_id, "access", timedelta(minutes=settings.jwt_access_token_minutes))


def create_refresh_token(user_id: str) -> str:
    return _create_token(user_id, "refresh", timedelta(days=settings.jwt_refresh_token_days))


def decode_token(token: str, expected_type: Literal["access", "refresh"]) -> dict[str, Any]:
    """Raises jwt.PyJWTError (or a ValueError for a type mismatch) on any failure."""
    payload = jwt.decode(
        token,
        settings.jwt_public_key,
        algorithms=["RS256"],
        issuer=settings.jwt_issuer,
    )
    if payload.get("type") != expected_type:
        raise ValueError(f"expected a {expected_type} token, got {payload.get('type')!r}")
    return payload
