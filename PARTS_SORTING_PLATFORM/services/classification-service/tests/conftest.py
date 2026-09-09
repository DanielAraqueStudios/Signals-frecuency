"""Test fixtures. No trained model exists in this test environment (there
is no labeled dataset yet -- see model/README.md), so every test here
exercises stub mode, which is the actual state app/infer.py should be in
right now. The MQTT publish is mocked -- these tests don't need a real
broker; ../../mqtt-broker/README.md documents how that was verified
separately."""

from __future__ import annotations

import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture()
def client():
    with patch("app.main.publish_result") as mock_publish:
        from app.main import app

        with TestClient(app) as test_client:
            test_client.mock_publish = mock_publish
            yield test_client


@pytest.fixture()
def sample_jpeg_bytes() -> bytes:
    """A small, synthetically-generated JPEG -- no external fixture file
    needed."""
    img = Image.new("RGB", (64, 64), color=(120, 80, 40))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()
