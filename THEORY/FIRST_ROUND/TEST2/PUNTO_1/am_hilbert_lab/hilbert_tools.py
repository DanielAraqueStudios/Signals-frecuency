"""Hilbert-transform analytic-signal envelope extraction."""

from __future__ import annotations

import numpy as np
from scipy.signal import hilbert


def hilbert_envelope(signal: np.ndarray) -> np.ndarray:
    """Magnitude of the analytic signal: `abs(scipy.signal.hilbert(signal))`."""
    return np.abs(hilbert(signal))
