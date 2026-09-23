"""Signal generation: time axes, the 60 Hz tone, and AM modulation.

`am_modulate` reimplements the same `(message) * (carrier)` AM scheme
`WORK_FIVE/am_lab.modulated_signal` uses, kept local so this folder stays
self-contained (see readme.md's note on task 6.1's cat-audio dependency).
"""

from __future__ import annotations

import numpy as np


def sample_times(duration_s: float, sample_rate: float) -> np.ndarray:
    """Builds a `[0, duration_s)` time axis at `sample_rate` samples/second."""
    n_samples = int(sample_rate * duration_s)
    return np.linspace(0, duration_s, n_samples, endpoint=False)


def tone_signal(t: np.ndarray, frequency_hz: float) -> np.ndarray:
    """Pure sine, `sin(2*pi*frequency_hz*t)`."""
    return np.sin(2 * np.pi * frequency_hz * t)


def am_modulate(message: np.ndarray, t: np.ndarray, carrier_freq_hz: float) -> np.ndarray:
    """AM-modulate `message` onto a carrier: `message * sin(2*pi*f_c*t)`.

    Same scheme as `WORK_FIVE/am_lab.modulated_signal`'s carrier term, but
    takes an arbitrary message signal (e.g. loaded cat audio) instead of a
    synthetic `2 + sin(...)` envelope.
    """
    return message * np.sin(2 * np.pi * carrier_freq_hz * t)
