"""The LMS adaptive filter itself, implemented from scratch (no library
adaptive-filter call) -- the point of the lab.

Update rule, applied sample by sample:

    y[n]   = w[n] . x_vec[n]          (FIR output, current tap-delay line)
    e[n]   = d[n] - y[n]              (error vs. desired signal)
    w[n+1] = w[n] + mu * e[n] * x_vec[n]
"""

from __future__ import annotations

import numpy as np


def run_lms(
    x: np.ndarray,
    d: np.ndarray,
    n_taps: int,
    mu: float,
    w_init: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Runs the LMS adaptive filter over `x` (input) against `d` (desired).

    Args:
        x: Input signal.
        d: Desired/reference signal, same length as `x`.
        n_taps: Number of FIR taps in the adaptive filter.
        mu: Step size (learning rate) of the LMS update.
        w_init: Optional initial weight vector (`n_taps`,); zeros if omitted.

    Returns:
        `(y, e, w_history)`: filter output, error signal, and the weight
        vector after every sample (`w_history.shape == (len(x), n_taps)`,
        row `n` holds `w[n]` *before* processing sample `n`).
    """
    n_samples = len(x)
    w = np.zeros(n_taps) if w_init is None else np.array(w_init, dtype=float)

    y = np.zeros(n_samples)
    e = np.zeros(n_samples)
    w_history = np.zeros((n_samples, n_taps))

    x_padded = np.concatenate([np.zeros(n_taps - 1), x])

    for n in range(n_samples):
        x_vec = x_padded[n : n + n_taps][::-1]
        w_history[n] = w
        y[n] = np.dot(w, x_vec)
        e[n] = d[n] - y[n]
        w = w + mu * e[n] * x_vec

    return y, e, w_history
