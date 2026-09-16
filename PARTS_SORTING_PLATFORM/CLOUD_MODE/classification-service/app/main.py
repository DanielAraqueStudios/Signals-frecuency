"""classification-service: receives a part photo from api-gateway,
classifies it via frequency-spectrum extraction (or honest stub mode --
see services/shared/spectrum_classifier.py), publishes the result to the
given MQTT topic, and returns the same JSON.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, File, Form, UploadFile

from app.config import settings
from app.mqtt_publisher import publish_result
from shared.spectrum_classifier import build_classifier

logger = logging.getLogger("classification-service")

app = FastAPI(title="classification-service")
classifier = build_classifier(settings.labels_config_path)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "stub_mode": classifier.is_stub}


@app.post("/classify")
async def classify(topic: str = Form(default=""), file: UploadFile = File(...)) -> dict:
    image_bytes = await file.read()
    result = classifier.classify(image_bytes)

    # topic is "" when api-gateway has no paired device for this upload
    # (device_id was omitted) -- a worker can classify a photo with no
    # ESP32-S3 nearby, in which case there's simply nothing to publish to.
    if topic:
        try:
            publish_result(topic, result)
        except Exception:
            # A device being offline/unreachable, or the broker being down
            # in local dev, must not turn a successful classification into
            # a 500 for the worker holding the phone -- the phone app
            # still gets its answer in the HTTP response either way.
            logger.exception("Failed to publish classification result to MQTT topic %s", topic)

    return result
