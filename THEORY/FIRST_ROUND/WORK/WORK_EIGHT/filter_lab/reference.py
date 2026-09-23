"""`scipy`-based reference filter, kept isolated from the manual path.

Used only for the item B "compare against Python's own function" step —
never for the manual coefficient derivation or manual filtering in
`coefficients.py` / `apply.py`.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, lfilter


def scipy_butter_lowpass(order: int, fc: float, fs: float, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Design a Butterworth low-pass with `scipy.signal.butter` and apply it
    with `scipy.signal.lfilter`.

    Args:
        order: Filter order.
        fc: Cutoff frequency, Hz.
        fs: Sample rate, Hz.
        x: Input signal.

    Returns:
        `(b, a, y)`.
    """
    b, a = butter(order, fc, btype="low", fs=fs)
    y = lfilter(b, a, x)
    return b, a, y
