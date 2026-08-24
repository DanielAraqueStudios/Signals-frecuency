"""Spectral and descriptive statistics shared by every exercise.

Provides the single-sided FFT magnitude spectrum, its dominant-frequency
peak, and basic descriptive statistics (mean, standard deviation) used
both by the synthetic-signal exercises (item 9) and by the audio
statistical-significance study (item 8, see `animal_analyzer/core.py`).
"""

from __future__ import annotations

import numpy as np


def compute_fft(signal: np.ndarray, sample_rate: float) -> tuple[np.ndarray, np.ndarray]:
    """Compute the single-sided, amplitude-normalized FFT of a real signal.

    Args:
        signal: Real-valued time-domain samples.
        sample_rate: Samples per second (Hz) the signal was captured/built at.

    Returns:
        `(frequencies, magnitude)`: non-negative frequency bins (Hz) from
        `np.fft.rfftfreq`, and the corresponding amplitude-normalized
        magnitude `(2/N) * |rfft(signal)|`.

    Raises:
        ValueError: If `signal` is empty.
    """
    n = len(signal)
    if n == 0:
        raise ValueError("signal must not be empty")

    spectrum = np.fft.rfft(signal)
    frequencies = np.fft.rfftfreq(n, d=1 / sample_rate)
    magnitude = (2 / n) * np.abs(spectrum)
    return frequencies, magnitude


def dominant_frequency(frequencies: np.ndarray, magnitude: np.ndarray) -> float:
    """Find the frequency of the largest spectral peak, ignoring DC (0 Hz).

    Args:
        frequencies: Frequency bins (Hz), as returned by `compute_fft`.
        magnitude: Magnitude at each bin, as returned by `compute_fft`.

    Returns:
        The frequency (Hz) of the largest non-DC peak. Falls back to bin 0
        if the spectrum has only one bin.
    """
    if len(magnitude) > 1:
        index = np.argmax(magnitude[1:]) + 1
    else:
        index = np.argmax(magnitude)
    return float(frequencies[index])


def signal_stats(signal: np.ndarray) -> dict[str, float]:
    """Compute basic descriptive statistics for a signal.

    Args:
        signal: Real-valued samples.

    Returns:
        `{"mean": ..., "std": ...}`.
    """
    return {"mean": float(np.mean(signal)), "std": float(np.std(signal))}
