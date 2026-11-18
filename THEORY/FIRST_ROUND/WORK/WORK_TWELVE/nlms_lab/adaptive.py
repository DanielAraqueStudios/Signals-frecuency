"""From-scratch NLMS and plain-LMS adaptive filters.

Both filters adapt an FIR weight vector `w` of length `filter_order` to
predict a desired signal `d[n]` from the most recent `filter_order` samples
of an input `x[n]`, one sample at a time. Neither calls a library's
built-in adaptive-filter routine -- the update rules are implemented here
directly from their closed-form definitions.
"""

from __future__ import annotations

import numpy as np


def nlms_filter(
    x: np.ndarray,
    d: np.ndarray,
    filter_order: int,
    mu: float = 0.5,
    eps: float = 1e-8,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Normalized LMS: `w[n+1] = w[n] + (mu / (eps + ||x_n||^2)) * e[n] * x_n`.

    `x_n` is the length-`filter_order` window of the most recent input
    samples (newest first) at step `n`; `e[n] = d[n] - w[n]^T x_n` is the
    a-priori error. The step size `mu` is normalized by the window's
    instantaneous energy `||x_n||^2`, so the *effective* step size
    `mu / (eps + ||x_n||^2)` shrinks automatically when the input is loud
    and grows when it is quiet -- this is what keeps NLMS's convergence
    rate roughly constant as the input power changes (see readme.md).

    Args:
        x: input sequence.
        d: desired sequence, same length as `x`.
        filter_order: number of FIR taps to adapt.
        mu: NLMS step size, normally in `(0, 2)` for stability.
        eps: small constant preventing division by zero when `||x_n||^2 -> 0`.

    Returns:
        `(weights_history, output, error)`: `weights_history` has shape
        `(len(x) + 1, filter_order)` (the weights *before* each update, plus
        the final weights); `output` and `error` have shape `(len(x),)`.
    """
    n_samples = len(x)
    w = np.zeros(filter_order)
    weights_history = np.zeros((n_samples + 1, filter_order))
    weights_history[0] = w
    output = np.zeros(n_samples)
    error = np.zeros(n_samples)

    x_padded = np.concatenate([np.zeros(filter_order - 1), x])
    for n in range(n_samples):
        x_window = x_padded[n : n + filter_order][::-1]
        y = w @ x_window
        e = d[n] - y
        energy = x_window @ x_window
        w = w + (mu / (eps + energy)) * e * x_window

        output[n] = y
        error[n] = e
        weights_history[n + 1] = w

    return weights_history, output, error


def lms_filter(
    x: np.ndarray,
    d: np.ndarray,
    filter_order: int,
    mu: float = 0.01,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Plain LMS: `w[n+1] = w[n] + mu * e[n] * x_n`, with a single fixed `mu`.

    Used only for the direct NLMS-vs-LMS comparison on a varying-power
    input (readme.md item 3) -- unlike NLMS, the step size here does not
    adapt to the input's instantaneous energy, so a single `mu` that is
    stable and fast at one power level is not necessarily either at another.

    Returns:
        Same shape convention as `nlms_filter`.
    """
    n_samples = len(x)
    w = np.zeros(filter_order)
    weights_history = np.zeros((n_samples + 1, filter_order))
    weights_history[0] = w
    output = np.zeros(n_samples)
    error = np.zeros(n_samples)

    x_padded = np.concatenate([np.zeros(filter_order - 1), x])
    for n in range(n_samples):
        x_window = x_padded[n : n + filter_order][::-1]
        y = w @ x_window
        e = d[n] - y
        w = w + mu * e * x_window

        output[n] = y
        error[n] = e
        weights_history[n + 1] = w

    return weights_history, output, error
