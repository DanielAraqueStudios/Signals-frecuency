"""local-server uses the trained YOLO weights (app/yolo_classifier.py),
which ARE present in this repo, so most tests here exercise real
inference rather than stub mode -- see test_local_server.py's module
docstring."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def sample_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (64, 64), color=(120, 80, 40))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()
