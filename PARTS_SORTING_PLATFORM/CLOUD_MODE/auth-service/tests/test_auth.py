"""Register -> login -> refresh round-trip, and the failure paths."""

from __future__ import annotations


def test_register_then_login(client):
    resp = client.post("/register", json={"email": "worker@example.com", "password": "hunter22"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "worker@example.com"

    resp = client.post("/login", json={"email": "worker@example.com", "password": "hunter22"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_register_duplicate_email_is_rejected(client):
    payload = {"email": "dup@example.com", "password": "hunter22"}
    assert client.post("/register", json=payload).status_code == 201
    resp = client.post("/register", json=payload)
    assert resp.status_code == 409


def test_login_wrong_password_is_rejected(client):
    client.post("/register", json={"email": "wrongpw@example.com", "password": "hunter22"})
    resp = client.post("/login", json={"email": "wrongpw@example.com", "password": "not-it"})
    assert resp.status_code == 401


def test_login_unknown_email_is_rejected(client):
    resp = client.post("/login", json={"email": "nobody@example.com", "password": "hunter22"})
    assert resp.status_code == 401


def test_refresh_issues_a_new_token_pair(client):
    client.post("/register", json={"email": "refresh@example.com", "password": "hunter22"})
    login_resp = client.post("/login", json={"email": "refresh@example.com", "password": "hunter22"})
    refresh_token = login_resp.json()["refresh_token"]

    resp = client.post("/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_refresh_rejects_an_access_token(client):
    client.post("/register", json={"email": "wrongtype@example.com", "password": "hunter22"})
    login_resp = client.post("/login", json={"email": "wrongtype@example.com", "password": "hunter22"})
    access_token = login_resp.json()["access_token"]

    resp = client.post("/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


def test_public_key_endpoint_exposes_the_verification_key(client):
    resp = client.get("/public-key")
    assert resp.status_code == 200
    body = resp.json()
    assert body["algorithm"] == "RS256"
    assert "BEGIN PUBLIC KEY" in body["public_key"]
