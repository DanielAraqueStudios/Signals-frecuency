"""Environment-driven configuration for local-server. This is the LAN
"computer" service -- no auth, no TLS, no MQTT (see ../README.md). WiFi
SSID/password are firmware-side (esp32_local_http.ino), not here."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    labels_config_path: str = "model/labels_config.json"


settings = Settings()
