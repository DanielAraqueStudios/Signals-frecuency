#!/usr/bin/env python3
"""Scans every address on the hotspot's /24 subnet and reports which ones
are alive, so you know exactly what's on the network before each run --
this computer (running local-server), the gateway (the phone hosting the
hotspot, which also runs the camera page), the ESP32, and the second
phone (volume-button pause trigger). A scan gives you IPs, not identities
-- it can't tell you "this IP is the camera phone" by itself, so cross-
check against what you expect to see (see check_network.py for this
computer's own IP + the gateway IP).

Usage:
    python scan_network.py
    python scan_network.py --timeout-ms 200   # faster but less reliable
"""

from __future__ import annotations

import argparse
import ipaddress
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from check_network import get_default_gateway, get_local_ip


def ping(ip: str, timeout_ms: int) -> bool:
    result = subprocess.run(
        ["ping", "-n", "1", "-w", str(timeout_ms), ip],
        capture_output=True, text=True, timeout=(timeout_ms / 1000) + 2,
    )
    return result.returncode == 0


def resolve_hostname(ip: str) -> str | None:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


def scan_subnet(local_ip: str, timeout_ms: int) -> list[str]:
    network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
    hosts = [str(ip) for ip in network.hosts()]

    alive: list[str] = []
    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = {executor.submit(ping, ip, timeout_ms): ip for ip in hosts}
        for future in as_completed(futures):
            ip = futures[future]
            try:
                if future.result():
                    alive.append(ip)
            except Exception:
                pass
    alive.sort(key=lambda ip: tuple(int(part) for part in ip.split(".")))
    return alive


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=300, help="ping timeout per host, in ms (default 300)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    local_ip = get_local_ip()
    gateway_ip = get_default_gateway()

    if not local_ip:
        print("ERROR: could not determine this computer's own IP -- is WiFi connected to the hotspot?")
        return 1

    print(f"Scanning {local_ip.rsplit('.', 1)[0]}.0/24 (this may take a few seconds)...")
    alive_ips = scan_subnet(local_ip, args.timeout_ms)

    print()
    print("===== Devices found on the network =====")
    for ip in alive_ips:
        tags = []
        if ip == local_ip:
            tags.append("THIS COMPUTER")
        if ip == gateway_ip:
            tags.append("HOTSPOT GATEWAY / likely camera phone")
        hostname = resolve_hostname(ip)
        tag_str = f"  [{', '.join(tags)}]" if tags else ""
        host_str = f" ({hostname})" if hostname else ""
        print(f"  {ip}{host_str}{tag_str}")

    if not alive_ips:
        print("  (none found -- check that this computer's WiFi is connected to the hotspot)")
    print("=========================================")
    print()
    print(
        f"{len(alive_ips)} device(s) found. Anything NOT tagged above is either the "
        "ESP32 or the second phone (volume-button trigger) -- cross-check by "
        "disconnecting one device at a time if you're unsure which IP is which."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
