"""Environment-driven configuration for classification-service.

Every value has a local-dev default so the service starts without a .env
file; production (Railway) overrides all of these via environment
variables. Never commit real secrets -- see ../../mqtt-broker/README.md
for how dev TLS certs and device credentials are generated locally, and
../../docs/deployment-railway.md for how they're injected in production.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # protected_namespaces=() -- pydantic reserves the "model_" prefix for
    # its own config by default, which collides with our model_path /
    # model_config field names below; this opts back out of that check.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", protected_namespaces=())

    # ONNX Runtime model. If model_path does not exist at startup, infer.py
    # runs in stub mode -- see app/infer.py.
    model_path: str = "model/weights/model.onnx"
    labels_path: str = "model/labels.json"

    # MQTT (TLS) -- matches ../../mqtt-broker/README.md's topic scheme and
    # connection parameters. mqtt_ca_cert may be either a filesystem path to
    # a PEM file or the PEM contents themselves (Railway env vars can't hold
    # a file, so mqtt_publisher.py accepts both -- see its docstring).
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 8883
    mqtt_ca_cert: str = "../../mqtt-broker/certs/ca.crt"
    mqtt_username: str = "classification-service"
    mqtt_password: str = ""


settings = Settings()
