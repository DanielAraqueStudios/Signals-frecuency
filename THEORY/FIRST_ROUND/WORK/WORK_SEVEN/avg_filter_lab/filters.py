"""Moving-average (boxcar) digital low-pass filter.

A moving-average filter of window length `N` is a normalized boxcar FIR
filter, `y[n] = (1/N) * sum_{k=0}^{N-1} x[n-k]`. Its frequency response is a
Dirichlet kernel (periodic sinc); the standard engineering approximation for
where that response crosses -3dB (the "cutoff") is:

    f_c ~= 0.443 * fs / N   =>   N = round(0.443 * fs / f_c)

(see e.g. Steven W. Smith, "The Scientist and Engineer's Guide to Digital
Signal Processing", ch. 15 — the 0.443 constant comes from solving
|sinc(0.443)| = 1/sqrt(2) for the boxcar's mainlobe).
"""

from __future__ import annotations

import numpy as np

CUTOFF_CONSTANT = 0.443


def cutoff_to_window(cutoff_hz: float, sample_rate: float) -> int:
    """Convert a target -3dB cutoff frequency to a moving-average window length.

    Args:
        cutoff_hz: Desired -3dB cutoff frequency (Hz).
        sample_rate: Sampling rate (Hz).

    Returns:
        Window length `N = round(0.443 * sample_rate / cutoff_hz)`, clamped to
        a minimum of 1 sample.

    Raises:
        ValueError: If `cutoff_hz` is not positive.
    """
    if cutoff_hz <= 0:
        raise ValueError("cutoff_hz must be positive")
    window = round(CUTOFF_CONSTANT * sample_rate / cutoff_hz)
    return max(1, window)


def moving_average_filter(signal: np.ndarray, window: int) -> np.ndarray:
    """Apply a boxcar moving-average filter of the given window length.

    Args:
        signal: 1-D input signal.
        window: Number of samples averaged per output point.

    Returns:
        The filtered signal, same length as `signal` (`mode="same"`
        convolution with a normalized boxcar kernel of length `window`).

    Raises:
        ValueError: If `window` is less than 1.
    """
    if window < 1:
        raise ValueError("window must be >= 1")
    kernel = np.ones(window) / window
    return np.convolve(signal, kernel, mode="same")


def moving_average_by_cutoff(
    signal: np.ndarray, cutoff_hz: float, sample_rate: float
) -> tuple[np.ndarray, int]:
    """Filter `signal` with a moving average sized for a target cutoff.

    Args:
        signal: 1-D input signal.
        cutoff_hz: Desired -3dB cutoff frequency (Hz).
        sample_rate: Sampling rate (Hz).

    Returns:
        `(filtered_signal, window_length)`.
    """
    window = cutoff_to_window(cutoff_hz, sample_rate)
    return moving_average_filter(signal, window), window
