#!/usr/bin/env python3
"""Single entry point for LOCAL_MODE: launches whichever of the other
scripts in this folder (run_training.py, run_server.py) you need, so you
never have to remember individual commands.

With no arguments, shows an interactive menu. With arguments, runs
non-interactively (useful for shortcuts/desktop icons/batch files):

    python main.py label                                  # labeling GUI
    python main.py train [--epochs N] [--imgsz N] ...   # just training
    python main.py serve [--host H] [--port P]           # just the server
    python main.py all                                    # label, train, then serve (interactive label step)

Note on "all": it runs the labeling GUI first (blocks until you close the
window), then training (minutes to hours depending on dataset
size/hardware -- GPU if available, see ../local-server/training/GPU_SETUP.md),
then starts the server -- in that order, never simultaneously (labeling
and training are one-off steps you do before deploying; the server is
the long-running process the phone/ESP32 talk to). If you only want the
server (the common case once a model already exists), use `serve`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
RUN_LABELING_GUI = SCRIPTS_DIR / "run_labeling_gui.py"
RUN_TRAINING = SCRIPTS_DIR / "run_training.py"
RUN_SERVER = SCRIPTS_DIR / "run_server.py"

MENU = """
LOCAL_MODE -- what do you want to run?
  1) Open the labeling GUI (load photos, assign class, auto-save to dataset/)
  2) Train the YOLO model
  3) Start the local server (for the phone/ESP32 on the hotspot LAN)
  4) All: label, then train, then start the server
  q) Quit
"""


def run_labeling_gui() -> int:
    return subprocess.run([sys.executable, str(RUN_LABELING_GUI)]).returncode


def run_training(extra_args: list[str]) -> int:
    return subprocess.run([sys.executable, str(RUN_TRAINING), *extra_args]).returncode


def run_server(extra_args: list[str]) -> int:
    return subprocess.run([sys.executable, str(RUN_SERVER), *extra_args]).returncode


def run_all() -> int:
    print("[main] Step 1/3: labeling GUI (close its window to continue)...")
    code = run_labeling_gui()
    if code != 0:
        print(f"[main] Labeling GUI exited with an error (code {code}), continuing anyway.", file=sys.stderr)

    print("[main] Step 2/3: training...")
    code = run_training([])
    if code != 0:
        print(f"[main] Training failed (exit {code}), not starting the server.", file=sys.stderr)
        return code

    print("[main] Step 3/3: starting server...")
    return run_server([])


def interactive_menu() -> int:
    while True:
        print(MENU)
        choice = input("> ").strip().lower()
        if choice == "1":
            return run_labeling_gui()
        if choice == "2":
            return run_training([])
        if choice == "3":
            return run_server([])
        if choice == "4":
            return run_all()
        if choice == "q":
            return 0
        print("Not a valid option, try again.")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        return interactive_menu()

    command, rest = args[0], args[1:]
    if command == "label":
        return run_labeling_gui()
    if command == "train":
        return run_training(rest)
    if command == "serve":
        return run_server(rest)
    if command == "all":
        return run_all()

    print(f"Unknown command '{command}'. Use: label | train | serve | all", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
