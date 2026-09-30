"""FIR (window-method) and IIR (Butterworth) filter design/application."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, firwin


def design_fir_lowpass(cutoff_hz: float, sample_rate: float, order: int = 100) -> np.ndarray:
    """Lowpass FIR filter via the window method (`scipy.signal.firwin`)."""
    nyquist = sample_rate / 2
    return firwin(order + 1, cutoff_hz / nyquist)


def design_iir_lowpass(cutoff_hz: float, sample_rate: float, order: int = 4):
    """Lowpass Butterworth IIR filter (`scipy.signal.butter`)."""
    nyquist = sample_rate / 2
    return butter(order, cutoff_hz / nyquist, btype="low")


def design_fir_bandpass(low_hz: float, high_hz: float, sample_rate: float, order: int = 50) -> np.ndarray:
    """Bandpass FIR filter via the window method (`scipy.signal.firwin`)."""
    nyquist = sample_rate / 2
    return firwin(order + 1, [low_hz / nyquist, high_hz / nyquist], pass_zero=False)


def design_iir_bandpass(low_hz: float, high_hz: float, sample_rate: float, order: int = 4):
    """Bandpass Butterworth IIR filter (`scipy.signal.butter`)."""
    nyquist = sample_rate / 2
    return butter(order, [low_hz / nyquist, high_hz / nyquist], btype="band")


def apply_filter(b: np.ndarray, a: np.ndarray, signal: np.ndarray) -> np.ndarray:
    """Zero-phase filter `signal` with coefficients `(b, a)` via `filtfilt`."""
    return filtfilt(b, a, signal)
