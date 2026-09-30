"""Single-sided FFT helper, amplitude-normalized."""

from __future__ import annotations

import numpy as np


def single_sided_fft(signal: np.ndarray, sample_rate: float, max_freq_hz: float | None = None):
    """Single-sided, amplitude-normalized FFT of `signal`.

    Returns `(frequencies, magnitude)`, restricted to `freqs >= 0` (and
    `<= max_freq_hz` if given).
    """
    n = signal.size
    freqs = np.fft.fftfreq(n, 1 / sample_rate)
    mask = freqs >= 0
    if max_freq_hz is not None:
        mask &= freqs <= max_freq_hz
    magnitude = np.abs(np.fft.fft(signal))[mask] / (n / 2)
    return freqs[mask], magnitude


def dominant_frequency(signal: np.ndarray, sample_rate: float, min_freq_hz: float = 0.0) -> float:
    """Frequency of the largest FFT magnitude above `min_freq_hz` (excludes DC by default via caller)."""
    freqs, mag = single_sided_fft(signal, sample_rate)
    valid = freqs >= min_freq_hz
    return float(freqs[valid][np.argmax(mag[valid])])
