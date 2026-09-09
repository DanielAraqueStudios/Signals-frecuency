"""Discrete convolution exercises applied to real audio (the "gato" recording).

Public API mirrors the split used in `WORK_THREE/signal_lab`: pure math in
`kernels.py`/`convolution.py`, audio I/O isolated in `audio.py`, figure
assembly in `plotting.py`.
"""

from __future__ import annotations

from .audio import load_audio
from .convolution import convolve
from .kernels import KERNELS, step_kernel
from .plotting import plot_convolution

__all__ = [
    "KERNELS",
    "step_kernel",
    "convolve",
    "load_audio",
    "plot_convolution",
]
