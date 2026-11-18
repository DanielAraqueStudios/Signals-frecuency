"""The 'unknown' FIR system to be identified (task 1): a fixed FIR filter
whose coefficients LMS never sees directly, only through its input/output.
"""

from __future__ import annotations

import numpy as np


def unknown_fir_coefficients() -> np.ndarray:
    """A fixed, arbitrary 5-tap FIR impulse response, treated as 'unknown'."""
    return np.array([0.6, -0.3, 0.45, -0.1, 0.2])


def apply_unknown_system(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    """Filters `x` through FIR coefficients `h` via linear convolution,
    truncated to `len(x)` samples (causal, same-length output).
    """
    return np.convolve(x, h)[: len(x)]
