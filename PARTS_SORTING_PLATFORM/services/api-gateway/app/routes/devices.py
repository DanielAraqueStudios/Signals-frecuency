"""ESP32-S3 device pairing: mints one MQTT credential per device, scoped
to the logged-in user in api-gateway's own database (see
../../mqtt-broker/README.md for why ownership lives here, not in the
MQTT topic string)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import verify_access_token
from app.models import Device
from app.mqtt_credentials import generate_password, provision_device_credential
from app.schemas import DevicePairResponse

router = APIRouter()


@router.post("/devices/pair", response_model=DevicePairResponse, status_code=201)
def pair_device(
    user_id: str = Depends(verify_access_token),
    db: Session = Depends(get_db),
) -> DevicePairResponse:
    mqtt_username = f"device-{uuid.uuid4().hex[:12]}"
    mqtt_password = generate_password()

    device = Device(user_id=user_id, mqtt_username=mqtt_username)
    db.add(device)
    db.commit()
    db.refresh(device)

    # Written to the DB first (source of truth for ownership) so a
    # broker-file write failure never leaves an orphaned, un-owned
    # credential behind.
    provision_device_credential(mqtt_username, mqtt_password)

    return DevicePairResponse(
        device_id=device.id,
        mqtt_username=mqtt_username,
        mqtt_password=mqtt_password,
        mqtt_broker_host=settings.mqtt_broker_host,
        mqtt_broker_port=settings.mqtt_broker_port,
        result_topic=f"results/{mqtt_username}",
    )
