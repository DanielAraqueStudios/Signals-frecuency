"""Minimal MQTT-over-TLS publisher: connect, publish one JSON message,
disconnect. Matches the broker's connection parameters and topic scheme
documented in ../../mqtt-broker/README.md.

This is a simple connect-publish-disconnect per call, which is fine for
this service's request volume (one photo classified at a time by a
worker). It is NOT optimized for high throughput -- a persistent,
reused connection would be a future improvement if this service ever
needs to publish many results per second.
"""

from __future__ import annotations

import json
import os
import ssl

import paho.mqtt.client as mqtt

from app.config import settings


def _ca_cert_file() -> str:
    """mqtt_ca_cert may be a filesystem path (local dev, docker-compose
    volume) or the raw PEM contents (Railway env vars can't hold a file
    directly). If it looks like PEM contents, write it to a temp file
    since paho-mqtt's tls_set() only accepts a file path."""
    value = settings.mqtt_ca_cert
    if "BEGIN CERTIFICATE" in value:
        import tempfile

        fd, path = tempfile.mkstemp(suffix=".pem")
        with os.fdopen(fd, "w") as f:
            f.write(value)
        return path
    return value


def publish_result(topic: str, payload: dict) -> None:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    client.tls_set(ca_certs=_ca_cert_file(), tls_version=ssl.PROTOCOL_TLS_CLIENT)

    client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, keepalive=10)
    client.loop_start()
    try:
        info = client.publish(topic, json.dumps(payload), qos=1)
        info.wait_for_publish(timeout=5)
    finally:
        client.loop_stop()
        client.disconnect()
