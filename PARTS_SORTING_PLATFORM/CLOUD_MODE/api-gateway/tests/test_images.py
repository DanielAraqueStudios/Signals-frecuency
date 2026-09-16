"""POST /images and GET /images -- classification-service is mocked
(httpx.AsyncClient), since it's a sibling service under separate test
coverage, not something this service's tests should depend on running."""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import make_access_token

_FAKE_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32  # minimal JPEG-like header, content is irrelevant here


def _mock_classification_response(label="bolt", confidence=0.87, stub=True):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={"label": label, "confidence": confidence, "stub": stub})
    return mock_resp


def test_upload_requires_auth(client):
    resp = client.post("/images", files={"image": ("part.jpg", io.BytesIO(_FAKE_JPEG), "image/jpeg")})
    assert resp.status_code == 401


def test_upload_rejects_unsupported_content_type(client):
    token = make_access_token()
    resp = client.post(
        "/images",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": ("part.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert resp.status_code == 415


def test_upload_classifies_and_stores_result(client):
    token = make_access_token("user-7")
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_mock_classification_response())

    with patch("app.routes.images.httpx.AsyncClient", return_value=mock_client):
        resp = client.post(
            "/images",
            headers={"Authorization": f"Bearer {token}"},
            files={"image": ("part.jpg", io.BytesIO(_FAKE_JPEG), "image/jpeg")},
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["label"] == "bolt"
    assert body["stub"] is True


def test_list_images_returns_only_the_caller_s_own(client):
    token_a = make_access_token("user-a")
    token_b = make_access_token("user-b")
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_mock_classification_response())

    with patch("app.routes.images.httpx.AsyncClient", return_value=mock_client):
        client.post(
            "/images",
            headers={"Authorization": f"Bearer {token_a}"},
            files={"image": ("part.jpg", io.BytesIO(_FAKE_JPEG), "image/jpeg")},
        )

    resp_a = client.get("/images", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = client.get("/images", headers={"Authorization": f"Bearer {token_b}"})
    assert len(resp_a.json()) == 1
    assert len(resp_b.json()) == 0


def test_upload_with_unknown_device_id_is_rejected(client):
    token = make_access_token("user-7")
    resp = client.post(
        "/images",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": ("part.jpg", io.BytesIO(_FAKE_JPEG), "image/jpeg")},
        data={"device_id": "does-not-exist"},
    )
    assert resp.status_code == 404
