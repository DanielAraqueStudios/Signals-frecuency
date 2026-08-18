"""Signal synthesis: sine, triangular, and Fourier-series square waves.

Vectorized NumPy/SciPy generators for the waveforms used across the
sampling exercises in this project: a pure sine (item 4), a square wave
rebuilt from a finite Fourier sine series alongside the mathematically
ideal square wave (items 5, 7, 9), and an offset triangular wave
(item 6).
"""

from __future__ import annotations

import numpy as np
from scipy import signal as scipy_signal


def angular_frequency(frequency_hz: float) -> float:
    """Convert an ordinary frequency (Hz) to an angular frequency (rad/s)."""
    return 2 * np.pi * frequency_hz


def sample_times(duration_s: float, sample_rate: float) -> np.ndarray:
    """Build a time axis sampled at `sample_rate` Hz over `duration_s` seconds.

    Args:
        duration_s: Length of the time window in seconds.
        sample_rate: Samples per second (Hz).

    Returns:
        Time values in seconds, spaced by 1/sample_rate, covering
        `[0, duration_s)`.
    """
    return np.arange(0, duration_s, 1 / sample_rate)


def sine_wave(t: np.ndarray, frequency_hz: float, amplitude: float = 1.0) -> np.ndarray:
    """Evaluate a pure sine wave at the given time samples.

    Args:
        t: Time samples (seconds).
        frequency_hz: Signal frequency (Hz).
        amplitude: Peak amplitude.

    Returns:
        `amplitude * sin(2*pi*frequency_hz*t)`.
    """
    return amplitude * np.sin(angular_frequency(frequency_hz) * t)


def square_wave_fourier(
    t: np.ndarray, w0: float, num_harmonics: int, amplitude: float = 1.0
) -> np.ndarray:
    """Reconstruct a square wave from a finite Fourier sine series.

    Sums the first `num_harmonics` odd harmonics (n = 1, 3, 5, ...,
    2*num_harmonics - 1) of the fundamental `w0`, each weighted by 1/n,
    per the standard square-wave Fourier series::

        x(t) = amplitude * (4/pi) * sum_{n odd} sin(n*w0*t) / n

    Args:
        t: Time samples (seconds) at which to evaluate the signal.
        w0: Fundamental angular frequency (rad/s).
        num_harmonics: Number of odd harmonics to sum. 1 yields a pure
            sine at the fundamental; larger values approach a square wave
            (with the persistent Gibbs overshoot near each discontinuity).
        amplitude: Target plateau amplitude of the reconstructed wave.

    Returns:
        The reconstructed signal, evaluated at each point in `t`.

    Raises:
        ValueError: If `num_harmonics` is less than 1.
    """
    if num_harmonics < 1:
        raise ValueError("num_harmonics must be >= 1")

    series = np.zeros_like(t, dtype=float)
    for i in range(num_harmonics):
        n = 2 * i + 1
        series += np.sin(n * w0 * t) / n
    return amplitude * (4 / np.pi) * series


def square_wave_ideal(t: np.ndarray, frequency_hz: float, amplitude: float = 1.0) -> np.ndarray:
    """Evaluate the mathematically ideal (infinite-bandwidth) square wave.

    Used as the reference signal in item 9, to compare against a
    truncated Fourier-series reconstruction (`square_wave_fourier`).

    Args:
        t: Time samples (seconds).
        frequency_hz: Signal frequency (Hz).
        amplitude: Plateau amplitude (+/-`amplitude`).

    Returns:
        `amplitude * square(2*pi*frequency_hz*t)`.
    """
    return amplitude * scipy_signal.square(angular_frequency(frequency_hz) * t)


def triangular_wave(t: np.ndarray, frequency_hz: float, v_max: float, v_min: float) -> np.ndarray:
    """Evaluate a triangular wave offset to swing between `v_min` and `v_max`.

    Built from SciPy's symmetric sawtooth (`width=0.5`, which produces a
    triangle rather than a ramp) on `[-1, 1]`, then rescaled so the
    plateaus land exactly on `v_min` and `v_max`.

    Args:
        t: Time samples (seconds).
        frequency_hz: Signal frequency (Hz).
        v_max: Peak (maximum) voltage.
        v_min: Trough (minimum) voltage.

    Returns:
        The triangular wave, in `[v_min, v_max]`.
    """
    unit_triangle = scipy_signal.sawtooth(angular_frequency(frequency_hz) * t, width=0.5)
    midpoint = (v_max + v_min) / 2
    half_span = (v_max - v_min) / 2
    return midpoint + half_span * unit_triangle
