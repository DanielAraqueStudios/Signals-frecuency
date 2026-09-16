"""Image upload -> classification, and the History listing."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import verify_access_token
from app.models import CapturedImage, Device
from app.schemas import ClassificationResult
from app.storage import upload_image

router = APIRouter()

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


@router.post("/images", response_model=ClassificationResult, status_code=status.HTTP_201_CREATED)
async def capture_image(
    image: UploadFile = File(...),
    device_id: str | None = Form(default=None),
    user_id: str = Depends(verify_access_token),
    db: Session = Depends(get_db),
) -> CapturedImage:
    if image.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "only image/jpeg and image/png are accepted")

    content = await image.read()
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty file")

    storage_key = upload_image(user_id, content, image.content_type)

    # device_id is optional: a worker can classify a photo without a
    # paired ESP32-S3 nearby (the result just won't be echoed to any
    # device over MQTT in that case). If provided, it must belong to the
    # requesting user -- this is exactly the ownership check the MQTT
    # topic string itself deliberately does NOT perform (see
    # ../../mqtt-broker/README.md).
    topic: str | None = None
    if device_id is not None:
        device = db.get(Device, device_id)
        if device is None or device.user_id != user_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "device not found")
        topic = f"results/{device.mqtt_username}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.classification_service_url}/classify",
                # Field name "file" and an always-present "topic" (empty
                # string when there's no paired device) must match
                # classification-service's POST /classify exactly -- see
                # ../../classification-service/app/main.py.
                files={"file": (image.filename, content, image.content_type)},
                data={"topic": topic or ""},
            )
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "classification service unavailable") from exc

    record = CapturedImage(
        user_id=user_id,
        storage_key=storage_key,
        label=result["label"],
        confidence=result.get("confidence"),
        stub=result.get("stub", True),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/images", response_model=list[ClassificationResult])
def list_images(
    user_id: str = Depends(verify_access_token),
    db: Session = Depends(get_db),
) -> list[CapturedImage]:
    stmt = select(CapturedImage).where(CapturedImage.user_id == user_id).order_by(CapturedImage.created_at.desc())
    return list(db.execute(stmt).scalars())
