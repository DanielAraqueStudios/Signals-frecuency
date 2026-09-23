"""Signal generation: the modulating tone and the AM signal it rides on."""

from __future__ import annotations

import numpy as np


def sample_times(duration_s: float, sample_rate: float) -> np.ndarray:
    """Builds a `[0, duration_s)` time axis at `sample_rate` samples/second."""
    n_samples = int(sample_rate * duration_s)
    return np.linspace(0, duration_s, n_samples, endpoint=False)


def tone_signal(t: np.ndarray, frequency_hz: float) -> np.ndarray:
    """Pure sine, `sin(2*pi*frequency_hz*t)`."""
    return np.sin(2 * np.pi * frequency_hz * t)


def modulated_signal(
    t: np.ndarray, message_freq_hz: float, carrier_freq_hz: float
) -> np.ndarray:
    """AM signal `(2 + sin(2*pi*f_msg*t)) * sin(2*pi*f_carrier*t)`."""
    return (2 + np.sin(2 * np.pi * message_freq_hz * t)) * np.sin(
        2 * np.pi * carrier_freq_hz * t
    )
