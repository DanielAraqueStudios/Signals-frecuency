"""Kernel (impulse response) vectors used across the convolution exercises.

Each kernel is a "step": the first half is `0`, the second half is `1`
(50%/50%, per the assignment). `step_kernel` builds one of any size, so
adding a third/fourth size later is a one-line addition to `KERNELS`
rather than a new hand-written vector.
"""

from __future__ import annotations

import numpy as np


def step_kernel(size: int) -> np.ndarray:
    """Build a 50%-zeros / 50%-ones step vector of length `size`.

    The first `size // 2` positions are `0`, the remaining
    `size - size // 2` positions are `1` — e.g. `step_kernel(10)` is
    `[0,0,0,0,0,1,1,1,1,1]`. For odd sizes the extra position goes to the
    `1`s half (`size - size // 2 >= size // 2`).

    Args:
        size: Number of positions in the kernel. Must be >= 1.

    Returns:
        A `float64` array of `0.0`s followed by `1.0`s, length `size`.

    Raises:
        ValueError: If `size < 1`.
    """
    if size < 1:
        raise ValueError(f"size must be >= 1, got {size}")
    n_zeros = size // 2
    n_ones = size - n_zeros
    return np.concatenate([np.zeros(n_zeros), np.ones(n_ones)])


# Third kernel: an explicit trapezoidal ramp (rise 0->1 over 5 steps,
# hold, fall 1->0 over 5 steps) rather than a generated step -- given as
# literal values, not built by `step_kernel`.
TRAPEZOID_10 = np.array([0, 0.25, 0.5, 0.75, 1, 1, 0.75, 0.5, 0.25, 0])

# Registry of the kernels used in `main.py`, keyed by the name used in
# plot titles / saved figure filenames. Add new ones here as they come up.
KERNELS: dict[str, np.ndarray] = {
    "step_10": step_kernel(10),
    "step_100": step_kernel(100),
    "trapezoid_10": TRAPEZOID_10,
}
