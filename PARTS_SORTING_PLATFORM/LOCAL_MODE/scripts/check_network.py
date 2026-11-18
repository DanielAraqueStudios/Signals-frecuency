#!/usr/bin/env python3
"""Prints every network address relevant to setting up LOCAL_MODE, from
this computer's side -- the Windows-side counterpart to the ESP32's own
printNetworkAddresses() (see ../firmware/esp32_local_http/esp32_local_http.ino),
so you know exactly what to type into a browser or into the firmware's
LOCAL_SERVER_HOST constant without hunting across devices.

Usage:
    python check_network.py
"""

from __future__ import annotations

import socket
import subprocess
import sys


def get_default_gateway() -> str | None:
    """The hotspot phone's own IP, when this PC is a client of its
    hotspot -- the phone IS the gateway in that topology."""
    try:
        output = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-NetIPConfiguration | Where-Object {$_.IPv4DefaultGateway} | "
             "Select-Object -First 1).IPv4DefaultGateway.NextHop"],
            capture_output=True, text=True, timeout=10,
        )
        gateway = output.stdout.strip()
        return gateway or None
    except Exception:
        return None


def get_local_ip() -> str | None:
    """This machine's own LAN IP (the one local-server should bind-visible
    as, and the one you'd put in the ESP32's LOCAL_SERVER_HOST)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return None


def main() -> int:
    local_ip = get_local_ip()
    gateway_ip = get_default_gateway()

    print("===== Network addresses (this computer's side) =====")
    print(f"This computer's own IP (local-server runs here): {local_ip or '(could not detect)'}")
    print(f"Hotspot gateway IP (the phone itself):            {gateway_ip or '(could not detect)'}")
    print()
    if local_ip:
        print(f"Put this in esp32_local_http.ino's LOCAL_SERVER_HOST: \"{local_ip}\"")
        print(f"local-server health check:   http://{local_ip}:8100/healthz")
        print(f"Pause-trigger endpoint:      http://{local_ip}:8100/band/pause")
    if gateway_ip:
        print(f"Phone's IP-camera app (if installed), typical port 8080: http://{gateway_ip}:8080")
    print("======================================================")
    print()
    print(
        "If the gateway IP above doesn't look right, make sure this "
        "computer's WiFi is actually connected to the phone's hotspot "
        "(not Ethernet/a different WiFi network)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
