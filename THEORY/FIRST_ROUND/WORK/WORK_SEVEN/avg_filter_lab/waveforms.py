"""Sine and square-wave versions of signals A and B, per WORK_FIVE.

`sine_tone`/`sine_am` reproduce WORK_FIVE's signals 2 and 1
(`am_lab.signals.tone_signal`/`modulated_signal`) verbatim. `square_tone`/
`square_am` are the same signals with every `sin(...)` term swapped for a
`scipy.signal.square(...)` of the same frequency, per Tarea 3-C.2, using the
square-wave generator already established in WORK_THREE
(`signal_lab.waveforms.square_wave_ideal`).
"""

from __future__ import annotations

import numpy as np
from scipy import signal as scipy_signal


def sample_times(duration_s: float, sample_rate: float) -> np.ndarray:
    """Builds a `[0, duration_s)` time axis at `sample_rate` samples/second."""
    return np.arange(0, duration_s, 1 / sample_rate)


def sine_tone(t: np.ndarray, frequency_hz: float) -> np.ndarray:
    """Signal A (sine case): `sin(2*pi*frequency_hz*t)`."""
    return np.sin(2 * np.pi * frequency_hz * t)


def sine_am(t: np.ndarray, message_freq_hz: float, carrier_freq_hz: float) -> np.ndarray:
    """Signal B (sine case): `(2 + sin(2*pi*f_msg*t)) * sin(2*pi*f_carrier*t)`."""
    return (2 + np.sin(2 * np.pi * message_freq_hz * t)) * np.sin(
        2 * np.pi * carrier_freq_hz * t
    )


def square_tone(t: np.ndarray, frequency_hz: float) -> np.ndarray:
    """Signal A (square case): `square(2*pi*frequency_hz*t)`."""
    return scipy_signal.square(2 * np.pi * frequency_hz * t)


def square_am(t: np.ndarray, message_freq_hz: float, carrier_freq_hz: float) -> np.ndarray:
    """Signal B (square case): `(2 + square(2*pi*f_msg*t)) * square(2*pi*f_carrier*t)`."""
    return (2 + scipy_signal.square(2 * np.pi * message_freq_hz * t)) * scipy_signal.square(
        2 * np.pi * carrier_freq_hz * t
    )
