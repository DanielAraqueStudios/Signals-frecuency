#!/usr/bin/env python3
"""Dedicated launcher for testing the full pipeline (pause/resume ->
photo -> classification + diameter) with the CURRENT trained weights,
nothing else -- no training, no labeling GUI. Just a thin wrapper around
run_server.py that confirms the configured weights file actually exists
before starting, so a typo/missing-file problem shows up immediately
instead of silently falling back to stub mode.

local-server already logs every step relevant to this test (see
app/main.py): "Band paused by ...", "Band resumed by ...", "Photo
received: sample_id=...", "Classified sample_id=...: label=... ...".
Just watch this terminal while you test with the ESP32 + both phones.

Usage:
    python run_pipeline_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
LOCAL_SERVER_DIR = SCRIPTS_DIR.parent / "local-server"
RUN_SERVER = SCRIPTS_DIR / "run_server.py"

sys.path.insert(0, str(LOCAL_SERVER_DIR))


def main() -> int:
    from app.config import settings

    weights_path = LOCAL_SERVER_DIR / settings.yolo_weights_path
    if not weights_path.exists():
        print(f"[run_pipeline_test] ERROR: configured weights not found: {weights_path}", file=sys.stderr)
        print(
            "[run_pipeline_test] Check app/config.py's yolo_weights_path, or train a model first "
            "(see ../local-server/training/README.md).",
            file=sys.stderr,
        )
        return 1

    print(f"[run_pipeline_test] Using weights: {weights_path}")
    print("[run_pipeline_test] Watch this terminal for: band pause/resume, photo received, classification result.")

    import subprocess
    result = subprocess.run([sys.executable, str(RUN_SERVER)])
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
