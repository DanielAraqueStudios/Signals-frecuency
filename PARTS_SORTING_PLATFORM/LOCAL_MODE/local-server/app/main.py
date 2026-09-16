"""local-server: the LAN "computer" in local-mode. Runs on a machine
joined to the same predefined WiFi access point as the phone and the
ESP32 (see ../README.md). No auth, no TLS, no MQTT -- plain HTTP,
explicitly unsecured for closed-LAN/demo use only. API surface is
GET/PUT only, as requested: PUT uploads an image and classifies it
synchronously; GET reads back a stored result.
"""

from __future__ import annotations

from fastapi import FastAPI, Request

from app.config import settings
from app.store import get_latest_result, get_result, save_result
from shared.spectrum_classifier import build_classifier

app = FastAPI(title="local-server")
classifier = build_classifier(settings.labels_config_path)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "stub_mode": classifier.is_stub}


@app.put("/images/{sample_id}")
async def put_image(sample_id: str, request: Request) -> dict:
    image_bytes = await request.body()
    result = classifier.classify(image_bytes)
    save_result(sample_id, result)
    return result


@app.get("/images/latest")
def get_latest_image_result() -> dict:
    result = get_latest_result()
    if result is None:
        return {"label": "unclassified", "confidence": None, "stub": True,
                 "reason": "no image submitted yet", "features": None}
    return result


@app.get("/images/{sample_id}")
def get_image_result(sample_id: str) -> dict:
    result = get_result(sample_id)
    if result is None:
        return {"label": "unclassified", "confidence": None, "stub": True,
                 "reason": f"no result stored for sample_id={sample_id}", "features": None}
    return result
