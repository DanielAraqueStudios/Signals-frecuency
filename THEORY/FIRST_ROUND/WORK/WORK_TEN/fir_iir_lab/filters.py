"""FIR (window-method) and IIR (Butterworth) lowpass filter design/application."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, firwin


def design_fir_lowpass(cutoff_hz: float, sample_rate: float, order: int = 100) -> np.ndarray:
    """Design a lowpass FIR filter via the window method (`scipy.signal.firwin`).

    Args:
        cutoff_hz: Passband edge, in Hz.
        sample_rate: Sampling rate, in Hz.
        order: Number of taps (filter length) minus 1; higher = sharper
            transition band, see readme.md's task 6.4 notes.

    Returns:
        FIR filter taps `b` (use with `apply_filter`, `a = [1.0]`).
    """
    nyquist = sample_rate / 2
    return firwin(order + 1, cutoff_hz / nyquist)


def design_iir_lowpass(cutoff_hz: float, sample_rate: float, order: int = 4):
    """Design a lowpass Butterworth IIR filter (`scipy.signal.butter`).

    Args:
        cutoff_hz: Passband edge, in Hz.
        sample_rate: Sampling rate, in Hz.
        order: Filter order; higher = sharper transition band but more
            ringing/instability risk, see readme.md's task 6.4 notes.

    Returns:
        `(b, a)` transfer-function coefficients.
    """
    nyquist = sample_rate / 2
    return butter(order, cutoff_hz / nyquist, btype="low")


def apply_filter(b: np.ndarray, a: np.ndarray, signal: np.ndarray) -> np.ndarray:
    """Zero-phase filter `signal` with coefficients `(b, a)` via `filtfilt`."""
    return filtfilt(b, a, signal)
