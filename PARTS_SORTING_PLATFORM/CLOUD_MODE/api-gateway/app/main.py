"""api-gateway entrypoint.

The only service the phone app talks to directly. Verifies JWTs issued by
auth-service, accepts authenticated image uploads, forwards them to
classification-service, and issues MQTT credentials to paired ESP32-S3
devices. See ../README.md and ../../docs/architecture.md.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.config import settings
from app.db import Base, engine
from app.routes.devices import router as devices_router
from app.routes.images import router as images_router
from app.storage import ensure_bucket_exists

logger = logging.getLogger("api-gateway")


async def _fetch_auth_public_key() -> None:
    """Populates settings.jwt_public_key from auth-service at startup, if
    it wasn't already provided via the JWT_PUBLIC_KEY env var directly."""
    if settings.jwt_public_key:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{settings.auth_service_url}/public-key")
            resp.raise_for_status()
            settings.jwt_public_key = resp.json()["public_key"]
    except httpx.HTTPError:
        logger.warning("could not fetch JWT public key from auth-service at startup; "
                        "every request will 503 until it's set (auth-service may still be starting)")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    ensure_bucket_exists()
    await _fetch_auth_public_key()
    yield


app = FastAPI(title="api-gateway", lifespan=lifespan)
app.include_router(images_router)
app.include_router(devices_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
