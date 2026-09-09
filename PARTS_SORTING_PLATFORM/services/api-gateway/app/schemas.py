"""Pydantic response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ClassificationResult(BaseModel):
    id: str
    label: str
    confidence: float | None
    stub: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DevicePairResponse(BaseModel):
    device_id: str
    mqtt_username: str
    mqtt_password: str  # returned once, at pairing time only -- never stored in plaintext
    mqtt_broker_host: str
    mqtt_broker_port: int
    result_topic: str
