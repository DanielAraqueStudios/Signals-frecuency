"""Synthetic multi-tone test signal for the filtering exercises."""

from __future__ import annotations

import numpy as np

# Reuses WORK_FIVE's sample rate for consistency across the assignment.
DEFAULT_FS = 10**5


def generate_test_signal(fs: int = DEFAULT_FS, duration_s: float = 0.05) -> tuple[np.ndarray, np.ndarray]:
    """A multi-tone signal spanning both cutoffs under test (40 Hz, 100 Hz)
    plus a clearly-above-cutoff tone that both filters should attenuate.

    Returns:
        `(t, x)` — time axis and signal, `x = sin(2*pi*20*t) + sin(2*pi*70*t)
        + sin(2*pi*400*t)`.
    """
    t = np.arange(0, duration_s, 1.0 / fs)
    x = (
        np.sin(2 * np.pi * 20 * t)
        + np.sin(2 * np.pi * 70 * t)
        + np.sin(2 * np.pi * 400 * t)
    )
    return t, x
