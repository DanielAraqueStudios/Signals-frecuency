"""FIR (order 50) and IIR Butterworth (order < 10) lowpass filters (task 2a)."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, firwin


def design_fir_lowpass(cutoff_hz: float, sample_rate: float, order: int = 50) -> np.ndarray:
    """Design a lowpass FIR filter via the window method (`scipy.signal.firwin`)."""
    nyquist = sample_rate / 2
    return firwin(order + 1, cutoff_hz / nyquist)


def design_iir_lowpass(cutoff_hz: float, sample_rate: float, order: int = 6):
    """Design a lowpass Butterworth IIR filter, order < 10 (`scipy.signal.butter`)."""
    nyquist = sample_rate / 2
    return butter(order, cutoff_hz / nyquist, btype="low")


def apply_filter(b: np.ndarray, a: np.ndarray, signal: np.ndarray) -> np.ndarray:
    """Zero-phase filter `signal` with coefficients `(b, a)` via `filtfilt`."""
    return filtfilt(b, a, signal)
