"""Mosquitto credential provisioning for newly-paired devices.

This replicates Mosquitto's own password-hash format (PBKDF2-HMAC-SHA512,
`$7$<iterations>$<salt-b64>$<hash-b64>`) in pure Python and appends a line
to the broker's shared password file, rather than shelling out to the
`mosquitto_passwd` CLI (which would require bundling mosquitto's binaries
into this image). Verified against a real Mosquitto 2.0.22 broker during
development -- see ../../mqtt-broker/README.md.

**Known limitation, stated plainly rather than glossed over:** Mosquitto's
file-based auth only re-reads the password file on SIGHUP or restart, so
a newly-paired device cannot authenticate until the mqtt-broker service
is restarted/reloaded. In docker-compose that's `docker compose restart
mqtt-broker`; a documented follow-up improvement (not built here) is
migrating to Mosquitto's dynamic-security plugin, which supports live
credential provisioning with no reload. See mqtt-broker/README.md.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets

from app.config import settings

_PBKDF2_ITERATIONS = 101  # matches mosquitto_passwd's own default


def generate_password() -> str:
    return secrets.token_urlsafe(24)


def _hash_password(password: str) -> str:
    salt = os.urandom(12)
    digest = hashlib.pbkdf2_hmac("sha512", password.encode(), salt, _PBKDF2_ITERATIONS, dklen=64)
    salt_b64 = base64.b64encode(salt).decode()
    digest_b64 = base64.b64encode(digest).decode()
    return f"$7${_PBKDF2_ITERATIONS}${salt_b64}${digest_b64}"


def provision_device_credential(mqtt_username: str, password: str) -> None:
    """Appends one `username:hash` line to the shared Mosquitto password
    file. Raises OSError if the shared volume isn't mounted/writable --
    that's a deployment misconfiguration, not something to swallow."""
    line = f"{mqtt_username}:{_hash_password(password)}\n"
    with open(settings.mqtt_passwd_file_path, "a", encoding="utf-8") as f:
        f.write(line)
