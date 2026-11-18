"""Train a YOLOv8 detector on the brocas/escariadores/tornillos dataset.

Requires training/requirements-training.txt installed separately (not part of
the server's own requirements.txt). GPU training needs a CUDA-enabled torch
build installed BEFORE requirements-training.txt (see GPU_SETUP.md in this
folder) -- plain `pip install torch` from requirements-training.txt alone
only gives you CPU. Usage:

    python train.py
    python train.py --epochs 150 --imgsz 640 --batch 16
    python train.py --device 0        # force first GPU
    python train.py --device cpu      # force CPU even if a GPU is present
"""
import argparse
import os
import tempfile
from pathlib import Path

import yaml
from ultralytics import YOLO

THIS_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_YAML = THIS_DIR / "data.yaml"


def resolve_data_yaml(data_yaml_path: str) -> str:
    """Ultralytics resolves a relative `path:` in data.yaml against its own
    global datasets_dir setting (e.g. training/datasets/), NOT against the
    folder data.yaml lives in -- so `path: .` in our data.yaml silently
    looked in training/datasets/dataset/... instead of training/dataset/...
    and failed with "images not found". Fix: write a temp copy of the yaml
    with `path` rewritten to an absolute path, and train from that instead."""
    src = Path(data_yaml_path).resolve()
    with open(src, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data["path"] = str(src.parent)

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=tempfile.gettempdir(), encoding="utf-8"
    )
    yaml.safe_dump(data, tmp, sort_keys=False, allow_unicode=True)
    tmp.close()
    return tmp.name


def detect_device() -> str:
    """Returns '0' (first GPU) if CUDA is available to torch, else 'cpu'.
    Ultralytics accepts this same string for its `device` argument."""
    try:
        import torch
        if torch.cuda.is_available():
            return "0"
    except ImportError:
        pass
    return "cpu"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train YOLOv8 on the parts-sorting dataset")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA_YAML), help="Path to data.yaml")
    parser.add_argument("--epochs", type=int, default=100, help="Max training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Training image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size (use -1 for auto)")
    parser.add_argument("--patience", type=int, default=20, help="Early-stopping patience (epochs with no improvement)")
    parser.add_argument(
        "--weights",
        type=str,
        default="yolov8n.pt",
        help="Starting checkpoint for transfer learning (auto-downloaded by ultralytics on first run)",
    )
    parser.add_argument("--project", type=str, default=str(THIS_DIR / "runs"), help="Where to write training runs")
    parser.add_argument("--name", type=str, default="parts_sorting", help="Run name under --project")
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="'0' for first GPU, 'cpu' to force CPU, or omit to auto-detect (GPU if torch sees one, else CPU)",
    )
    parser.add_argument(
        "--amp",
        type=str,
        choices=["true", "false"],
        default="false",
        help="Mixed-precision training. Defaults to 'false': GTX 16xx-series GPUs "
             "(Turing without Tensor Cores, e.g. GTX 1650) are known to produce "
             "NaN losses from epoch 1 with AMP enabled under Ultralytics. Pass "
             "'true' to re-enable it (e.g. on a GPU with Tensor Cores, for speed).",
    )
    parser.add_argument(
        "--require-gpu",
        action="store_true",
        help="Fail immediately instead of silently training on CPU if no GPU is detected. "
             "Run check_gpu.py first to diagnose before using this.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0 if os.name == "nt" else 8,
        help="DataLoader worker processes. Defaults to 0 on Windows: PyTorch's "
             "multiprocessing DataLoader workers can crash with "
             "'OSError: WinError 6: The handle is invalid' when launched from "
             "some terminals/background processes on Windows -- 0 disables "
             "multiprocessing (slightly slower data loading, but reliable). "
             "Raise this if you confirm multiprocessing workers are stable on your setup.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = args.device if args.device is not None else detect_device()

    if args.require_gpu and device == "cpu":
        print(
            "ERROR: --require-gpu was set but no GPU was detected (or --device cpu was forced).\n"
            "Run 'python check_gpu.py' to see exactly why, then fix per GPU_SETUP.md."
        )
        raise SystemExit(1)

    print(f"Training device: {device} ({'GPU' if device != 'cpu' else 'CPU'})")

    resolved_data_yaml = resolve_data_yaml(args.data)

    model = YOLO(args.weights)
    model.train(
        data=resolved_data_yaml,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        project=args.project,
        name=args.name,
        device=device,
        workers=args.workers,
        amp=(args.amp == "true"),
    )

    best_weights = Path(args.project) / args.name / "weights" / "best.pt"
    print(f"\nTraining complete. Best weights (if training succeeded): {best_weights}")


if __name__ == "__main__":
    main()
