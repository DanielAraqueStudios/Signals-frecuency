"""POST /devices/pair: auth enforcement, credential shape, and that the
credential actually lands in the shared Mosquitto password file."""

from __future__ import annotations

from tests.conftest import make_access_token


def test_pair_device_requires_auth(client):
    resp = client.post("/devices/pair")
    assert resp.status_code == 401


def test_pair_device_issues_scoped_credential(client):
    token = make_access_token("user-42")
    resp = client.post("/devices/pair", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["mqtt_username"].startswith("device-")
    assert body["mqtt_password"]
    assert body["result_topic"] == f"results/{body['mqtt_username']}"


def test_pair_device_writes_to_the_shared_passwd_file(client, monkeypatch):
    from app.config import settings

    token = make_access_token("user-42")
    resp = client.post("/devices/pair", headers={"Authorization": f"Bearer {token}"})
    mqtt_username = resp.json()["mqtt_username"]

    with open(settings.mqtt_passwd_file_path, encoding="utf-8") as f:
        contents = f.read()
    assert mqtt_username in contents
    assert contents.strip().split(":")[1].startswith("$7$101$")  # Mosquitto PBKDF2 format


def test_rejects_a_refresh_token(client):
    import jwt as pyjwt
    from datetime import datetime, timedelta, timezone
    from tests.conftest import _PRIVATE_KEY

    now = datetime.now(timezone.utc)
    refresh_token = pyjwt.encode(
        {"sub": "user-1", "type": "refresh", "iss": "parts-sorting-auth-service",
         "iat": now, "exp": now + timedelta(days=30)},
        _PRIVATE_KEY, algorithm="RS256",
    )
    resp = client.post("/devices/pair", headers={"Authorization": f"Bearer {refresh_token}"})
    assert resp.status_code == 401
