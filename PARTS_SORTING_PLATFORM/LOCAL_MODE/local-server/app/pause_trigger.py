"""In-memory "band paused" state -- replaces the VL53L0X distance
sensor's signal (object detected under the camera) with a network
signal, since that sensor isn't working reliably on the physical rig.

A second device (an Android phone, fixed IP on the same LAN) has two
buttons: POST /band/pause sets paused=True, POST /band/resume sets it
back to False. The ESP32 (esp32_local_http.ino) polls
GET /band/pause-status alongside its existing /images/latest poll and
keeps the band stopped for as long as paused stays True -- this is a
level, not a one-shot edge: unlike an earlier version of this module,
reading the status does NOT reset it. The band resumes only when
/band/resume is explicitly called.

Process-lifetime only, same intentional simplification as store.py (no
DB, no persistence across restarts -- see ../README.md)."""

from __future__ import annotations

from threading import Lock

_band_paused = False
_lock = Lock()


def set_paused(paused: bool) -> None:
    global _band_paused
    with _lock:
        _band_paused = paused


def is_paused() -> bool:
    with _lock:
        return _band_paused
