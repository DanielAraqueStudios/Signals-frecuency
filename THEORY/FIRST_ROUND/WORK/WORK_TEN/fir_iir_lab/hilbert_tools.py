"""Hilbert-transform envelope extraction (tasks 6.2/6.3).

Unlike `spectrum.remove_negative_frequencies` (a hand-rolled FFT step),
this module explicitly calls `scipy.signal.hilbert`, as the assignment
names "transformada de Hilbert" directly for these tasks.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import hilbert


def hilbert_envelope(signal: np.ndarray) -> np.ndarray:
    """Magnitude of the analytic signal: `abs(scipy.signal.hilbert(signal))`."""
    return np.abs(hilbert(signal))
