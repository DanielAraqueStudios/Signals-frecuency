"""Test fixtures: in-memory SQLite DB, a matching RSA dev keypair (so
JWT_PUBLIC_KEY is pre-set and the lifespan never needs a real
auth-service call), a stubbed S3 upload, and a temp MQTT passwd file --
none of api-gateway's real external dependencies (Postgres, MinIO,
auth-service, classification-service, the MQTT broker) need to be running
for these tests."""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def _generate_rsa_pem_pair() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


_PRIVATE_KEY, _PUBLIC_KEY = _generate_rsa_pem_pair()
os.environ["JWT_PUBLIC_KEY"] = _PUBLIC_KEY
os.environ["JWT_ISSUER"] = "parts-sorting-auth-service"


def make_access_token(user_id: str = "user-1") -> str:
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "iss": "parts-sorting-auth-service",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }
    return jwt.encode(payload, _PRIVATE_KEY, algorithm="RS256")


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr("app.storage.ensure_bucket_exists", lambda: None)
    monkeypatch.setattr("app.storage.upload_image", lambda user_id, content, content_type: f"{user_id}/fake-key.jpg")

    passwd_file = tmp_path / "passwd"
    passwd_file.write_text("")
    from app.config import settings as app_settings
    monkeypatch.setattr(app_settings, "mqtt_passwd_file_path", str(passwd_file))

    from app.db import Base
    from app.db import get_db as real_get_db
    from app.main import app

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[real_get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
