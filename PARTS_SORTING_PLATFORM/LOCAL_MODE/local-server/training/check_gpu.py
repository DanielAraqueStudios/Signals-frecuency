"""Standalone GPU verification -- run this BEFORE train.py to know for sure
whether training will use the GPU or silently fall back to CPU.

Usage:
    python check_gpu.py

Checks, in order:
1. Is `nvidia-smi` on PATH and does it report a GPU? (driver-level check,
   works even without torch installed)
2. Is `torch` importable, and does `torch.cuda.is_available()` return True?
   (this is the check that actually matters for training)
"""
from __future__ import annotations

import shutil
import subprocess
import sys


def check_nvidia_smi() -> bool:
    if shutil.which("nvidia-smi") is None:
        print("[1/2] nvidia-smi not found on PATH -- no NVIDIA driver detected, or not installed.")
        return False
    result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[1/2] nvidia-smi ran but returned an error:\n{result.stderr}")
        return False
    print("[1/2] nvidia-smi OK -- driver sees a GPU:")
    for line in result.stdout.splitlines():
        if "GeForce" in line or "Driver Version" in line or "RTX" in line or "Quadro" in line or "Tesla" in line:
            print(f"      {line.strip()}")
    return True


def check_torch_cuda() -> bool:
    try:
        import torch
    except ImportError:
        print("[2/2] 'torch' is not installed -- training WILL run on CPU.")
        print("      See GPU_SETUP.md: install a CUDA-enabled torch build before requirements-training.txt.")
        return False

    print(f"[2/2] torch {torch.__version__} importable.")
    if torch.cuda.is_available():
        print(f"      torch.cuda.is_available() = True -- GPU: {torch.cuda.get_device_name(0)}")
        return True

    print("      torch.cuda.is_available() = False -- this torch build has NO CUDA support,")
    print("      or the driver/CUDA version mismatch is blocking it. Training WILL run on CPU.")
    print("      See GPU_SETUP.md to install the correct CUDA-enabled build.")
    return False


def main() -> int:
    driver_ok = check_nvidia_smi()
    torch_ok = check_torch_cuda()

    print()
    if driver_ok and torch_ok:
        print("RESULT: GPU training is ready. `python train.py` will use the GPU automatically.")
        return 0
    if driver_ok and not torch_ok:
        print("RESULT: GPU is present but torch can't use it yet. Fix per GPU_SETUP.md, then re-run this check.")
        return 1
    print("RESULT: No usable NVIDIA GPU detected. Training will run on CPU unless this is fixed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
