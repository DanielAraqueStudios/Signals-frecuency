#!/usr/bin/env python3
"""Launches the PyQt6 "pipeline" GUI (../local-server/pipeline_gui.py):
pick which trained weights to use, start/stop local-server, and watch its
logs (band pause/resume, photo received, classification results) live in
the window. Installs requirements-gui.txt automatically if PyQt6 isn't
importable yet. Also needs requirements-training.txt installed (for
ultralytics) -- not auto-installed here, same reasoning as
run_test_image_gui.py.

Usage:
    python run_pipeline_gui.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
LOCAL_SERVER_DIR = SCRIPTS_DIR.parent / "local-server"
PIPELINE_GUI_SCRIPT = LOCAL_SERVER_DIR / "pipeline_gui.py"
REQUIREMENTS_FILE = LOCAL_SERVER_DIR / "requirements-gui.txt"


def ensure_gui_deps() -> None:
    try:
        import PyQt6  # noqa: F401
        return
    except ImportError:
        pass
    print(f"[run_pipeline_gui] Missing PyQt6 -- installing from {REQUIREMENTS_FILE}")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
        check=True,
    )


def main() -> int:
    if not PIPELINE_GUI_SCRIPT.exists():
        print(f"[run_pipeline_gui] ERROR: {PIPELINE_GUI_SCRIPT} not found", file=sys.stderr)
        return 1

    try:
        import ultralytics  # noqa: F401
    except ImportError:
        print(
            "[run_pipeline_gui] ERROR: ultralytics is not installed. "
            "Run: pip install -r ../local-server/training/requirements-training.txt",
            file=sys.stderr,
        )
        return 1

    ensure_gui_deps()

    print(f"[run_pipeline_gui] Launching {PIPELINE_GUI_SCRIPT}")
    result = subprocess.run([sys.executable, str(PIPELINE_GUI_SCRIPT)])
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
