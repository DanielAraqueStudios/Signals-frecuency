"""Single-sided FFT for spectral evidence (task 2a)."""

from __future__ import annotations

import numpy as np


def single_sided_fft(signal: np.ndarray, sample_rate: float) -> tuple[np.ndarray, np.ndarray]:
    """Amplitude-normalized single-sided spectrum `(freqs_hz, magnitude)`."""
    n = len(signal)
    spectrum = np.fft.fft(signal)
    freqs = np.fft.fftfreq(n, d=1.0 / sample_rate)
    half = n // 2
    magnitude = (2.0 / n) * np.abs(spectrum[:half])
    return freqs[:half], magnitude
