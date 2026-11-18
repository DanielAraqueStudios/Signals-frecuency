"""local-server: the LAN "computer" in local-mode. Runs on a machine
joined to the same predefined WiFi access point as the phone and the
ESP32 (see ../README.md). No auth, no TLS, no MQTT -- plain HTTP,
explicitly unsecured for closed-LAN/demo use only. API surface is
GET/PUT only, as requested: PUT uploads an image and classifies it
synchronously; GET reads back a stored result.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse

from app.config import settings
from app.diameter_measurement import measure_diameter_cm
from app.pause_trigger import is_paused, set_paused
from app.store import get_latest_result, get_result, save_result
from app.yolo_classifier import build_classifier

app = FastAPI(title="local-server")
classifier = build_classifier(settings.yolo_weights_path)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Explicit level + handler: uvicorn's own logging config doesn't raise the
# root logger above WARNING, so a bare getLogger().info() call here would
# silently never print without this.
logger = logging.getLogger("local_server")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "stub_mode": classifier.is_stub}


# ---------------------------------------------------------------------
# Phone camera page -- opened ONCE in the hotspot phone's own browser.
# It's a plain static page (static/camera.html): no native app, the page
# itself polls GET /band/pause-status and PUTs captured frames to
# /images/{sample_id} as an outbound client, since a browser tab can't
# accept incoming connections. See that file for the capture/upload logic.
# ---------------------------------------------------------------------
@app.get("/camera")
def get_camera_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "camera.html")


# ---------------------------------------------------------------------
# Zero-install pause-trigger page for device #2. Browsers can't
# intercept hardware volume-key presses, so instead of an automation
# app, this phone opens this page once and taps the on-screen button,
# which POSTs to /band/pause -- same effect as a volume-key press would
# have had via an automation app. See static/pause_button.html.
# ---------------------------------------------------------------------
@app.get("/pause-button")
def get_pause_button_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "pause_button.html")


@app.put("/images/{sample_id}")
async def put_image(sample_id: str, request: Request) -> dict:
    image_bytes = await request.body()
    client_host = request.client.host if request.client else "unknown"
    logger.info("Photo received: sample_id=%s from %s (%d bytes)", sample_id, client_host, len(image_bytes))

    result = classifier.classify(image_bytes)

    # Diameter is a separate measurement (black 1cm marker calibration,
    # see app/diameter_measurement.py) on the SAME photo, merged into the
    # one result so a single /images/latest poll gives the ESP32 both the
    # classification and the diameter to show on its LCD -- never raises;
    # diameter_cm is None with a `reason` if the marker/part weren't found.
    diameter_result = measure_diameter_cm(image_bytes)
    result["diameter_cm"] = diameter_result["diameter_cm"]
    result["diameter_reason"] = diameter_result["reason"]

    logger.info(
        "Classified sample_id=%s: label=%s confidence=%s diameter_cm=%s",
        sample_id, result.get("label"), result.get("confidence"), result.get("diameter_cm"),
    )

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


# ---------------------------------------------------------------------
# Band pause/resume -- stands in for the VL53L0X distance sensor while
# it isn't working reliably. A second device (phone) on the LAN has two
# buttons (static/pause_button.html): POST /band/pause stops the band,
# POST /band/resume starts it again. This is a LEVEL, not a one-shot
# edge -- the band stays paused until /band/resume is called; the ESP32
# just polls GET /band/pause-status and matches the motor to whatever
# state it reports. See app/pause_trigger.py.
# ---------------------------------------------------------------------
@app.post("/band/pause")
def trigger_band_pause(request: Request) -> dict:
    logger.info("Band paused by %s (device #2 / phone)", request.client.host if request.client else "unknown")
    set_paused(True)
    return {"status": "ok", "pause_requested": True}


@app.post("/band/resume")
def trigger_band_resume(request: Request) -> dict:
    logger.info("Band resumed by %s (device #2 / phone)", request.client.host if request.client else "unknown")
    set_paused(False)
    return {"status": "ok", "pause_requested": False}


@app.get("/band/pause-status")
def get_band_pause_status() -> dict:
    return {"pause_requested": is_paused()}
