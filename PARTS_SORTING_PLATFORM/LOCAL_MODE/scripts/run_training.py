#!/usr/bin/env python3
"""Runs the YOLO training pipeline (../local-server/training/train.py) without
requiring the user to cd/activate a venv manually. Installs
requirements-training.txt on first use if ultralytics isn't importable, then
forwards all CLI args straight to train.py (e.g. `--epochs 50 --imgsz 640`).

Usage:
    python run_training.py [--epochs N] [--imgsz N] [--batch N] [--data PATH]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
TRAINING_DIR = SCRIPTS_DIR.parent / "local-server" / "training"
TRAIN_SCRIPT = TRAINING_DIR / "train.py"
REQUIREMENTS_FILE = TRAINING_DIR / "requirements-training.txt"


def ensure_training_deps() -> None:
    try:
        import ultralytics  # noqa: F401
        return
    except ImportError:
        pass
    print(f"[run_training] 'ultralytics' not found -- installing from {REQUIREMENTS_FILE}")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
        check=True,
    )


def main() -> int:
    if not TRAIN_SCRIPT.exists():
        print(f"[run_training] ERROR: {TRAIN_SCRIPT} not found", file=sys.stderr)
        return 1

    ensure_training_deps()

    extra_args = sys.argv[1:]
    print(f"[run_training] Launching {TRAIN_SCRIPT} {' '.join(extra_args)}")
    result = subprocess.run([sys.executable, str(TRAIN_SCRIPT), *extra_args])
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
