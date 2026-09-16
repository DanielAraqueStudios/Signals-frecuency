"""Environment-driven configuration for api-gateway.

Every value has a local-dev default so docker-compose works with no .env
file; Railway overrides all of these via service environment variables.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/parts_sorting"

    # auth-service: api-gateway verifies JWTs locally using this public key
    # rather than calling back to auth-service on every request. Three ways
    # to provide it, in priority order: JWT_PUBLIC_KEY (literal PEM, e.g.
    # pasted into a Railway env var), JWT_PUBLIC_KEY_FILE (a mounted file
    # path -- what docker-compose.yml uses, since env vars can't cleanly
    # hold multi-line PEM text), or leave both unset and it's fetched once
    # at startup from GET {auth_service_url}/public-key.
    auth_service_url: str = "http://auth-service:8000"
    jwt_public_key: str = ""
    jwt_public_key_file: str = ""
    jwt_issuer: str = "parts-sorting-auth-service"

    def model_post_init(self, __context: object) -> None:
        if not self.jwt_public_key and self.jwt_public_key_file:
            self.jwt_public_key = Path(self.jwt_public_key_file).read_text(encoding="utf-8")

    classification_service_url: str = "http://classification-service:8000"

    # S3-compatible object storage for captured images (Cloudflare R2,
    # Backblaze B2, AWS S3, MinIO for local dev -- anything boto3 can talk
    # to via a custom endpoint_url). Railway has no built-in object
    # storage, so this is deliberately vendor-agnostic.
    s3_endpoint_url: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "parts-sorting-images"
    s3_region: str = "auto"

    # MQTT credentials this service itself doesn't need (it never
    # publishes/subscribes) -- device pairing only *writes* a new
    # credential into the broker's shared password file; see
    # app/mqtt_credentials.py for MQTT_PASSWD_FILE_PATH.
    mqtt_broker_host: str = "mqtt-broker"
    mqtt_broker_port: int = 8883
    mqtt_passwd_file_path: str = "/shared/mqtt/passwd"


settings = Settings()
