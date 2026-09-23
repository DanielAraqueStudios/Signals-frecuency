"""Tarea 2, Parte 1 (Parte 2 del enunciado): the six correlation vectors and
the "multiply each vector against the first n samples of the cat audio, sum,
store" procedure, generalized to fill a 100-element output vector.

Interpretation of the assignment text
--------------------------------------
The assignment gives a single worked example per vector (`Vector1` dotted
against the *first* 10 audio samples gives one output value) but then asks
for a 100-element output vector from only 6 fixed-length vectors — six
single dot products can only produce six numbers, not 100. The literal
example is a **correlation at lag 0**: `sum(vector[k] * audio[k])`. The
natural generalization that reproduces that example as its first term is a
**sliding dot product** (discrete cross-correlation, "valid" mode): slide
each vector across the audio one sample at a time and record
`sum(vector[k] * audio[start + k])` for `start = 0, 1, 2, ...`.

Each of the 6 vectors therefore contributes a *block* of consecutive lag-0,
lag-1, ... sliding correlation values, and the six blocks are concatenated
in `Vector1..Vector6` order to build the 100-element output vector, with the
100 slots split as evenly as possible across the 6 vectors (`100 = 6*16 + 4`,
so the first 4 vectors contribute 17 values and the last 2 contribute 16).
This choice is implemented explicitly (not guessed silently) so it is easy
to audit or replace.
"""

from __future__ import annotations

import numpy as np

VECTORS: dict[str, np.ndarray] = {
    "Vector1": np.ones(10),
    "Vector2": np.zeros(10),
    "Vector3": np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0], dtype=np.float64),
    "Vector4": np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1], dtype=np.float64),
    "Vector5": np.array([0, 0.25, 0.5, 0.75, 1, 1, 1, 0.75, 0.25, 0], dtype=np.float64),
    "Vector6": np.array(
        [0, 0.25, 0.5, 0.75, 1, 1, 0.75, 0.5, 0.25, 0, 0, -0.25, -0.5, -0.75, -1, -1, -0.75, -0.5, -0.25, 0],
        dtype=np.float64,
    ),
}

TOTAL_OUTPUT_LENGTH = 100


def sliding_correlation(vector: np.ndarray, signal: np.ndarray, n_values: int) -> np.ndarray:
    """Slide `vector` across `signal` one sample at a time, dotting each time.

    `out[i] = sum(vector[k] * signal[i + k] for k in range(len(vector)))`,
    for `i = 0 .. n_values - 1`. `out[0]` is exactly the assignment's worked
    example (vector dotted with the first `len(vector)` samples).

    Args:
        vector: One of the fixed correlation vectors.
        signal: The audio signal (or any 1-D array) to slide across.
        n_values: Number of sliding positions to compute.

    Returns:
        Array of length `n_values`.

    Raises:
        ValueError: If `signal` is too short to slide `n_values` times.
    """
    vector = np.asarray(vector, dtype=np.float64)
    signal = np.asarray(signal, dtype=np.float64)
    needed = vector.size + n_values - 1
    if signal.size < needed:
        raise ValueError(f"signal has {signal.size} samples, needs at least {needed}")
    return np.array([np.dot(vector, signal[i:i + vector.size]) for i in range(n_values)])


def _split_counts(total: int, n_parts: int) -> list[int]:
    """Split `total` into `n_parts` integer counts as evenly as possible.

    The remainder is distributed to the earliest parts first, e.g.
    `_split_counts(100, 6) == [17, 17, 17, 17, 16, 16]`.
    """
    base, remainder = divmod(total, n_parts)
    return [base + 1 if i < remainder else base for i in range(n_parts)]


def correlation_vector_100(signal: np.ndarray) -> np.ndarray:
    """Build the 100-element output vector for Tarea 2 / Parte 1.

    Runs `sliding_correlation` for each of `Vector1..Vector6` against
    `signal`, with the 100 output slots split as evenly as possible across
    the 6 vectors (see module docstring), and concatenates the per-vector
    blocks in `Vector1..Vector6` order.

    Args:
        signal: The cat audio signal.

    Returns:
        A length-100 array of sliding dot-product values.
    """
    counts = _split_counts(TOTAL_OUTPUT_LENGTH, len(VECTORS))
    blocks = [
        sliding_correlation(vector, signal, count)
        for vector, count in zip(VECTORS.values(), counts)
    ]
    return np.concatenate(blocks)
