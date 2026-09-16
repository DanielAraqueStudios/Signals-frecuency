"""PUT /images/{id} and GET /images/{id}|latest, end-to-end against the
FastAPI app -- no reference profiles configured in this test environment,
so every classification is stub mode (see model/labels_config.json)."""

from __future__ import annotations


def test_healthz_reports_stub_mode(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "stub_mode": True}


def test_get_latest_before_any_put_is_a_documented_stub(client):
    resp = client.get("/images/latest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["stub"] is True
    assert body["reason"] == "no image submitted yet"


def test_put_image_classifies_and_stores_result(client, sample_jpeg_bytes):
    resp = client.put("/images/sample-1", content=sample_jpeg_bytes)
    assert resp.status_code == 200
    body = resp.json()
    assert body["stub"] is True
    assert body["label"] == "unclassified"
    assert body["reason"] == "no reference spectrum profiles configured"


def test_get_by_id_returns_the_same_result_that_was_put(client, sample_jpeg_bytes):
    put_resp = client.put("/images/sample-2", content=sample_jpeg_bytes)
    get_resp = client.get("/images/sample-2")
    assert get_resp.status_code == 200
    assert get_resp.json() == put_resp.json()


def test_get_latest_returns_most_recently_put_result(client, sample_jpeg_bytes):
    client.put("/images/sample-3", content=sample_jpeg_bytes)
    client.put("/images/sample-4", content=sample_jpeg_bytes)

    latest_resp = client.get("/images/latest")
    by_id_resp = client.get("/images/sample-4")
    assert latest_resp.json() == by_id_resp.json()


def test_get_unknown_id_returns_documented_stub_not_404(client):
    resp = client.get("/images/never-submitted")
    assert resp.status_code == 200
    body = resp.json()
    assert body["stub"] is True
    assert "never-submitted" in body["reason"]
