#!/usr/bin/env python3
"""Launches the PyQt6 labeling GUI (../local-server/training/label_gui.py),
installing requirements-gui.txt automatically if PyQt6 isn't importable yet.

Usage:
    python run_labeling_gui.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
TRAINING_DIR = SCRIPTS_DIR.parent / "local-server" / "training"
LABEL_GUI_SCRIPT = TRAINING_DIR / "label_gui.py"
REQUIREMENTS_FILE = TRAINING_DIR / "requirements-gui.txt"


def ensure_gui_deps() -> None:
    missing = []
    try:
        import PyQt6  # noqa: F401
    except ImportError:
        missing.append("PyQt6")
    try:
        import yaml  # noqa: F401
    except ImportError:
        missing.append("yaml (pyyaml)")
    if not missing:
        return
    print(f"[run_labeling_gui] Missing {', '.join(missing)} -- installing from {REQUIREMENTS_FILE}")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
        check=True,
    )


def main() -> int:
    if not LABEL_GUI_SCRIPT.exists():
        print(f"[run_labeling_gui] ERROR: {LABEL_GUI_SCRIPT} not found", file=sys.stderr)
        return 1

    ensure_gui_deps()

    print(f"[run_labeling_gui] Launching {LABEL_GUI_SCRIPT}")
    result = subprocess.run([sys.executable, str(LABEL_GUI_SCRIPT)])
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
