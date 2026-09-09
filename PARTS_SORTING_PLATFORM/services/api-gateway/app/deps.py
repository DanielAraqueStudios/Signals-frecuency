"""JWT verification dependency.

api-gateway verifies access tokens issued by auth-service locally, using
only its RS256 public key (fetched once at startup from
GET {auth_service_url}/public-key, or provided directly via
JWT_PUBLIC_KEY) -- it never calls back to auth-service per-request.
"""

from __future__ import annotations

import jwt
from fastapi import Header, HTTPException, status

from app.config import settings


def verify_access_token(authorization: str | None = Header(default=None)) -> str:
    """Returns the authenticated user's id (the token's `sub` claim).

    `authorization` is Optional (not FastAPI's Header(...) required-field
    shortcut) so a missing header reaches this function's own 401, rather
    than FastAPI auto-responding 422 before our auth logic ever runs.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    token = authorization.removeprefix("Bearer ")

    if not settings.jwt_public_key:
        # Fail loudly rather than silently accepting unverifiable tokens.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "auth verification key not configured")

    try:
        payload = jwt.decode(
            token,
            settings.jwt_public_key,
            algorithms=["RS256"],
            issuer=settings.jwt_issuer,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh tokens cannot be used here")

    return payload["sub"]
