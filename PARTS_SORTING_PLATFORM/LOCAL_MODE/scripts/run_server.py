#!/usr/bin/env python3
"""Starts local-server (../local-server) with uvicorn bound to 0.0.0.0, so
the phone and ESP32 on the hotspot LAN can reach it -- without the user
typing the uvicorn command/host/port by hand each time.

Usage:
    python run_server.py [--host 0.0.0.0] [--port 8100] [--reload]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
LOCAL_SERVER_DIR = SCRIPTS_DIR.parent / "local-server"
REQUIREMENTS_FILE = LOCAL_SERVER_DIR / "requirements.txt"
# app/main.py imports shared.spectrum_classifier, which lives in
# PARTS_SORTING_PLATFORM/shared/ -- two levels up from local-server/, not
# on the path by default. Without this, uvicorn fails with
# "ModuleNotFoundError: No module named 'shared'".
PARTS_SORTING_PLATFORM_DIR = SCRIPTS_DIR.parent.parent


def ensure_server_deps() -> None:
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        return
    except ImportError:
        pass
    print(f"[run_server] Missing dependency -- installing from {REQUIREMENTS_FILE}")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local-server with uvicorn")
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default: 0.0.0.0, LAN-reachable)")
    parser.add_argument("--port", type=int, default=8100, help="port (default: 8100, matches firmware default)")
    parser.add_argument("--reload", action="store_true", help="auto-reload on code changes (dev only)")
    return parser.parse_args()


def main() -> int:
    if not LOCAL_SERVER_DIR.exists():
        print(f"[run_server] ERROR: {LOCAL_SERVER_DIR} not found", file=sys.stderr)
        return 1

    ensure_server_deps()
    args = parse_args()

    cmd = [
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", args.host, "--port", str(args.port),
    ]
    if args.reload:
        cmd.append("--reload")

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{PARTS_SORTING_PLATFORM_DIR}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(PARTS_SORTING_PLATFORM_DIR)
    )

    print(f"[run_server] Launching: {' '.join(cmd)} (cwd={LOCAL_SERVER_DIR})")
    result = subprocess.run(cmd, cwd=str(LOCAL_SERVER_DIR), env=env)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
