"""LMS adaptive-filter lab: system identification, adaptive noise
cancellation, and a step-size (mu) convergence sweep.

Public API mirrors the split used in `WORK_TEN/fir_iir_lab`: pure math per
module, `main.py` only wires them together and plots.
"""

from __future__ import annotations

from .signals import sample_times, tone_signal, white_noise
from .lms import run_lms
from .unknown_system import unknown_fir_coefficients, apply_unknown_system
from .audio import load_audio

__all__ = [
    "sample_times",
    "tone_signal",
    "white_noise",
    "run_lms",
    "unknown_fir_coefficients",
    "apply_unknown_system",
    "load_audio",
]
