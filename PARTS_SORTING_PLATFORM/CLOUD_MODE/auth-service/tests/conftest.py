"""Test fixtures: an isolated in-memory SQLite DB and a matching RSA
dev keypair, both generated fresh per test session so tests never depend
on a real Postgres instance or committed secrets."""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

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
os.environ["JWT_PRIVATE_KEY"] = _PRIVATE_KEY
os.environ["JWT_PUBLIC_KEY"] = _PUBLIC_KEY


@pytest.fixture()
def client():
    # Imported here, after the env vars above are set, so app.config.settings
    # picks up the test keypair/DB instead of the real .env defaults.
    from app.db import Base
    from app.main import app
    from app.db import get_db as real_get_db

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
