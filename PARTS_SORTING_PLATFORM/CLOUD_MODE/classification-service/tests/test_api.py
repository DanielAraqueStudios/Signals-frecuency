"""POST /classify end-to-end in stub mode (no model.onnx present in this
test environment -- see model/README.md), with the MQTT publish mocked."""

from __future__ import annotations


def test_healthz_reports_stub_mode(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["stub_mode"] is True


def test_classify_returns_stub_response_and_publishes_it(client, sample_jpeg_bytes):
    resp = client.post(
        "/classify",
        data={"topic": "results/device-testABC"},
        files={"file": ("part.jpg", sample_jpeg_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {
        "label": "unclassified",
        "confidence": None,
        "stub": True,
        "reason": "no reference spectrum profiles configured",
        "features": None,
    }

    client.mock_publish.assert_called_once_with("results/device-testABC", body)


def test_classify_still_returns_result_when_mqtt_publish_fails(client, sample_jpeg_bytes):
    client.mock_publish.side_effect = ConnectionRefusedError("broker unreachable")

    resp = client.post(
        "/classify",
        data={"topic": "results/device-testABC"},
        files={"file": ("part.jpg", sample_jpeg_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["stub"] is True


def test_classify_with_no_topic_skips_publish(client, sample_jpeg_bytes):
    """api-gateway sends topic="" when a photo has no paired device (see
    ../../api-gateway/app/routes/images.py) -- nothing should be
    published in that case, and the request must still succeed."""
    resp = client.post(
        "/classify",
        data={"topic": ""},
        files={"file": ("part.jpg", sample_jpeg_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["stub"] is True
    client.mock_publish.assert_not_called()


def test_classify_with_omitted_topic_field_also_skips_publish(client, sample_jpeg_bytes):
    """topic now defaults to "" rather than being a required field, so a
    caller that omits it entirely (not just sends it empty) must not 422."""
    resp = client.post(
        "/classify",
        files={"file": ("part.jpg", sample_jpeg_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    client.mock_publish.assert_not_called()
