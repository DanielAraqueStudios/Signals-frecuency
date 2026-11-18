#!/usr/bin/env python3
"""Launches the PyQt6 "test the model on one image" GUI
(../local-server/training/test_image_gui.py), installing requirements-gui.txt
automatically if PyQt6 isn't importable yet. Also needs
requirements-training.txt installed (for ultralytics) -- not auto-installed
here since that one's heavier (torch) and the training scripts already
cover it.

Usage:
    python run_test_image_gui.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
TRAINING_DIR = SCRIPTS_DIR.parent / "local-server" / "training"
TEST_IMAGE_GUI_SCRIPT = TRAINING_DIR / "test_image_gui.py"
REQUIREMENTS_FILE = TRAINING_DIR / "requirements-gui.txt"


def ensure_gui_deps() -> None:
    missing = []
    try:
        import PyQt6  # noqa: F401
    except ImportError:
        missing.append("PyQt6")
    try:
        import PIL  # noqa: F401
    except ImportError:
        missing.append("Pillow")
    if not missing:
        return
    print(f"[run_test_image_gui] Missing {', '.join(missing)} -- installing from {REQUIREMENTS_FILE}")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
        check=True,
    )


def main() -> int:
    if not TEST_IMAGE_GUI_SCRIPT.exists():
        print(f"[run_test_image_gui] ERROR: {TEST_IMAGE_GUI_SCRIPT} not found", file=sys.stderr)
        return 1

    try:
        import ultralytics  # noqa: F401
    except ImportError:
        print(
            "[run_test_image_gui] ERROR: ultralytics is not installed. "
            "Run: pip install -r ../local-server/training/requirements-training.txt",
            file=sys.stderr,
        )
        return 1

    ensure_gui_deps()

    print(f"[run_test_image_gui] Launching {TEST_IMAGE_GUI_SCRIPT}")
    result = subprocess.run([sys.executable, str(TEST_IMAGE_GUI_SCRIPT)])
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
