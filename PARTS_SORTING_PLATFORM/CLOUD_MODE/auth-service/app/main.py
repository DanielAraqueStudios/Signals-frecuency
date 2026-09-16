"""auth-service entrypoint.

Owns user accounts and JWT issuance (RS256). Other services never touch
the users table directly -- they verify the tokens this service issues
using only the public key (see app.config.settings.jwt_public_key), which
is why /public-key exists: it's how the other services fetch it at
startup instead of it being copy-pasted into each one's config.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db import Base, engine
from app.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="auth-service", lifespan=lifespan)
app.include_router(auth_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/public-key")
def public_key() -> dict[str, str]:
    """Lets api-gateway (and anyone else) fetch the RS256 public key to
    verify tokens locally, without calling back into this service on
    every request."""
    return {"public_key": settings.jwt_public_key, "algorithm": "RS256"}
