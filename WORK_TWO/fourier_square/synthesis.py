"""Fourier-series synthesis of a band-limited square wave.

Reconstructs a periodic square wave from the first N terms of its Fourier
sine series (odd harmonics only, each weighted by 1/n) — the classic
example used to illustrate Gibbs phenomenon and the effect of sampling
rate on a reconstructed continuous-time signal. All synthesis is
vectorized with NumPy.
"""

from __future__ import annotations

import numpy as np

# Default fundamental: w0 = 6*pi*k for k=1 -> f0 = w0/(2*pi) = 3 Hz.
DEFAULT_FUNDAMENTAL_HZ = 3.0
DEFAULT_DURATION_S = 1.0


def angular_frequency(frequency_hz: float) -> float:
    """Convert an ordinary frequency (Hz) to an angular frequency (rad/s)."""
    return 2 * np.pi * frequency_hz


def sample_times(duration_s: float, sample_rate: int) -> np.ndarray:
    """Build a time axis sampled at `sample_rate` Hz over `duration_s` seconds.

    Args:
        duration_s: Length of the time window in seconds.
        sample_rate: Samples per second (Hz).

    Returns:
        Time values in seconds, spaced by 1/sample_rate, covering
        `[0, duration_s)`.
    """
    return np.arange(0, duration_s, 1 / sample_rate)


def fourier_square_wave(t: np.ndarray, w0: float, num_harmonics: int) -> np.ndarray:
    """Reconstruct a unit-amplitude square wave from its Fourier sine series.

    Sums the first `num_harmonics` odd harmonics (n = 1, 3, 5, ...,
    2*num_harmonics - 1) of the fundamental `w0`, each weighted by 1/n, per
    the standard square-wave Fourier series::

        x(t) = (4/pi) * sum_{n odd} sin(n*w0*t) / n

    Args:
        t: Time samples (seconds) at which to evaluate the signal.
        w0: Fundamental angular frequency (rad/s).
        num_harmonics: Number of odd harmonics to sum. 1 yields a pure
            sine at the fundamental; larger values approach a square wave
            (with the persistent Gibbs overshoot near each discontinuity).

    Returns:
        The reconstructed signal, evaluated at each point in `t`.

    Raises:
        ValueError: If `num_harmonics` is less than 1.
    """
    if num_harmonics < 1:
        raise ValueError("num_harmonics must be >= 1")

    signal = np.zeros_like(t, dtype=float)
    for i in range(num_harmonics):
        n = 2 * i + 1
        signal += np.sin(n * w0 * t) / n
    return (4 / np.pi) * signal
