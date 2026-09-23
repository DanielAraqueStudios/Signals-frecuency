"""Difference-equation application via an explicit `for` loop.

The assignment requires filtering to be done "con ciclo for" over the
input/output vectors — no `scipy.signal.lfilter`/`filtfilt` in the manual
path. This module is that loop, used for both item A (single biquad) and
item B (cascaded biquads).
"""

from __future__ import annotations

import numpy as np


def apply_difference_equation(b: np.ndarray, a: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Apply an IIR filter `(b, a)` to `x` via the direct-form-I difference
    equation, computed sample-by-sample:

        a[0]*y[n] = sum_k b[k]*x[n-k] - sum_{k>=1} a[k]*y[n-k]

    Args:
        b: Numerator (feed-forward) coefficients.
        a: Denominator (feedback) coefficients, `a[0] != 0`.
        x: Input signal, 1-D.

    Returns:
        `y`, same length as `x`.
    """
    b = np.asarray(b, dtype=np.float64)
    a = np.asarray(a, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    if a[0] == 0:
        raise ValueError("a[0] must be non-zero")

    n_b, n_a = b.size, a.size
    y = np.zeros(x.size, dtype=np.float64)
    for n in range(x.size):
        acc = 0.0
        for k in range(n_b):
            if n - k >= 0:
                acc += b[k] * x[n - k]
        for k in range(1, n_a):
            if n - k >= 0:
                acc -= a[k] * y[n - k]
        y[n] = acc / a[0]
    return y


def apply_cascade(sections: list[tuple[np.ndarray, np.ndarray]], x: np.ndarray) -> np.ndarray:
    """Run `x` through each `(b, a)` section in series, each via the same
    for-loop difference equation (equivalent to convolving the sections'
    polynomials into one higher-order filter, done here stage-by-stage).
    """
    y = np.asarray(x, dtype=np.float64)
    for b, a in sections:
        y = apply_difference_equation(b, a, y)
    return y
