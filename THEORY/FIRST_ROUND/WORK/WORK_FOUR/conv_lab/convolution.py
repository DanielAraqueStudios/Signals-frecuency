"""Discrete convolution: a textbook direct-sum implementation, plus the
NumPy-backed version actually used to filter full-length audio.

Both exist on purpose: `manual_convolve` spells out
`y[n] = sum_k x[k] * h[n-k]` exactly as taught, so it's the one to read to
understand the math; `convolve` (thin `np.convolve` wrapper) is what
`main.py` runs against the real audio, since a Python-level double loop
over ~44,100 samples/second of audio would be too slow to be usable.
`tests/test_convolution.py` checks they agree.
"""

from __future__ import annotations

import numpy as np


def manual_convolve(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    """Direct-sum discrete convolution, `mode="full"`.

    Implements `y[n] = sum_{k=0}^{len(x)-1} x[k] * h[n-k]` term by term
    (no FFT, no `np.convolve`) so the computation matches the definition
    used in the assignment. Output length is `len(x) + len(h) - 1`.

    Args:
        x: Input signal, 1-D.
        h: Kernel / impulse response, 1-D.

    Returns:
        The full discrete convolution `x * h`.

    Raises:
        ValueError: If either input is empty.
    """
    x = np.asarray(x, dtype=np.float64)
    h = np.asarray(h, dtype=np.float64)
    if x.size == 0 or h.size == 0:
        raise ValueError("x and h must both be non-empty")

    n_out = x.size + h.size - 1
    y = np.zeros(n_out, dtype=np.float64)
    for n in range(n_out):
        total = 0.0
        # k ranges over the values where both x[k] and h[n-k] exist.
        k_min = max(0, n - h.size + 1)
        k_max = min(x.size - 1, n)
        for k in range(k_min, k_max + 1):
            total += x[k] * h[n - k]
        y[n] = total
    return y


def convolve(x: np.ndarray, h: np.ndarray, mode: str = "full") -> np.ndarray:
    """Discrete convolution via `numpy.convolve` (fast path for real audio).

    Args:
        x: Input signal, 1-D.
        h: Kernel / impulse response, 1-D.
        mode: `"full"`, `"same"`, or `"valid"` — forwarded to
            `numpy.convolve`.

    Returns:
        `x * h`, per `numpy.convolve`'s `mode` semantics.

    Raises:
        ValueError: If either input is empty.
    """
    x = np.asarray(x, dtype=np.float64)
    h = np.asarray(h, dtype=np.float64)
    if x.size == 0 or h.size == 0:
        raise ValueError("x and h must both be non-empty")
    return np.convolve(x, h, mode=mode)
