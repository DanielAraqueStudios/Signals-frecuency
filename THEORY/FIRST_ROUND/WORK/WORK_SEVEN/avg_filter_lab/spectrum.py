"""FFT helper: single-sided, amplitude-normalized magnitude spectrum.

Same implementation as WORK_FIVE's `am_lab.spectrum.single_sided_fft`.
"""

from __future__ import annotations

import numpy as np


def single_sided_fft(
    signal: np.ndarray, sample_rate: float, max_freq_hz: float | None = None
):
    """Single-sided, amplitude-normalized FFT of `signal`.

    Args:
        signal: Real-valued time-domain signal, 1-D.
        sample_rate: Sampling rate in Hz.
        max_freq_hz: If given, drop bins above this frequency.

    Returns:
        `(frequencies, magnitude)`, both restricted to `freqs >= 0`
        (and `<= max_freq_hz` if given).
    """
    n = signal.size
    freqs = np.fft.fftfreq(n, 1 / sample_rate)
    mask = freqs >= 0
    if max_freq_hz is not None:
        mask &= freqs <= max_freq_hz
    magnitude = np.abs(np.fft.fft(signal))[mask] / (n / 2)
    return freqs[mask], magnitude
