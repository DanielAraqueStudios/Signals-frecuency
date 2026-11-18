"""Signal generation: time axes, tones, and noise.

`tone_signal` matches `WORK_TEN/fir_iir_lab.signals.tone_signal`'s closed
form, kept local so this folder stays self-contained.
"""

from __future__ import annotations

import numpy as np


def sample_times(duration_s: float, sample_rate: float) -> np.ndarray:
    """Builds a `[0, duration_s)` time axis at `sample_rate` samples/second."""
    n_samples = int(sample_rate * duration_s)
    return np.linspace(0, duration_s, n_samples, endpoint=False)


def tone_signal(t: np.ndarray, frequency_hz: float, amplitude: float = 1.0) -> np.ndarray:
    """Pure sine, `amplitude * sin(2*pi*frequency_hz*t)`."""
    return amplitude * np.sin(2 * np.pi * frequency_hz * t)


def white_noise(n_samples: int, power: float, rng: np.random.Generator) -> np.ndarray:
    """Zero-mean Gaussian white noise with the given variance (`power`)."""
    return rng.normal(0.0, np.sqrt(power), n_samples)
