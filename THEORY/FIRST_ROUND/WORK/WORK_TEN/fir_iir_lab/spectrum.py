"""FFT helpers: single-sided spectrum, and explicit negative-frequency removal.

`remove_negative_frequencies` builds the analytic signal by hand (FFT, zero
the negative-frequency half, IFFT) rather than calling `scipy.signal.hilbert`
for it -- that call is used explicitly, and only, in `hilbert_tools.py` for
tasks 6.2/6.3.
"""

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


def remove_negative_frequencies(signal: np.ndarray) -> np.ndarray:
    """Zero out negative-frequency FFT bins, then inverse-FFT.

    For a real input this produces (twice) the analytic signal's positive-
    frequency content -- exactly the first step `scipy.signal.hilbert`
    performs internally -- but is done explicitly here via `numpy.fft`
    per the assignment's "quitarle la parte negativa" instruction.

    Args:
        signal: Real- or complex-valued 1-D signal.

    Returns:
        Complex-valued signal with all negative-frequency bins zeroed.
    """
    n = signal.size
    spectrum = np.fft.fft(signal)
    freqs = np.fft.fftfreq(n)
    spectrum[freqs < 0] = 0
    return np.fft.ifft(spectrum)
