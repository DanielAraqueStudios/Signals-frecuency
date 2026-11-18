# LOCAL_MODE/scripts

Python wrappers so you don't need to remember individual terminal commands
for each piece of LOCAL_MODE.

- `run_labeling_gui.py` -- opens the PyQt6 labeling GUI
  (`../local-server/training/label_gui.py`): load photos, click the part's
  class, it auto-saves the image + YOLO label into
  `../local-server/training/dataset/{images,labels}/{train,val}/` for you.
  Installs `requirements-gui.txt` automatically if `PyQt6` isn't installed yet.
- `run_training.py` -- runs `../local-server/training/train.py` (installs
  `requirements-training.txt` automatically if `ultralytics` isn't
  installed yet). Forwards any CLI args, e.g.
  `python run_training.py --epochs 50`, `python run_training.py --device 0`
  (GPU) -- see `../local-server/training/GPU_SETUP.md` for getting a
  CUDA-enabled torch installed first.
- `run_server.py` -- starts `local-server` with uvicorn bound to
  `0.0.0.0` (so the phone/ESP32 on the hotspot LAN can reach it),
  installing `requirements.txt` automatically if needed.
  `python run_server.py --port 8100`.
- `main.py` -- the single entry point. Run it with no arguments for an
  interactive menu, or non-interactively:
  - `python main.py label` -- labeling GUI only
  - `python main.py train` -- training only
  - `python main.py serve` -- server only (the common case once a model exists)
  - `python main.py all` -- labeling GUI, then training, then the server
    (sequential, not simultaneous -- see the docstring in `main.py`)

## Requirements

Python 3.9+ on PATH as `python` (or run with `python3` on the same
scripts). Each script installs its own dependencies on first run via
`pip install -r <requirements file>`; nothing extra needs installing to
run the scripts themselves.

## What was not verified

Not run in this environment (no real dataset, GPU, or ESP32/phone
hardware available). `run_server.py`'s underlying `uvicorn app.main:app`
command matches what `../local-server/README.md` documents and was
exercised there; the wrapper script itself (argument parsing, dependency
auto-install) was not executed end-to-end.
