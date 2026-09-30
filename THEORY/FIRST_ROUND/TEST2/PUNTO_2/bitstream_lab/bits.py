"""Envelope -> per-bit square wave -> bits (task 2b/2c)."""

from __future__ import annotations

import numpy as np

from .filters import apply_filter, design_fir_lowpass


def smooth_envelope(envelope: np.ndarray, sample_rate: float, bit_period_s: float) -> np.ndarray:
    """Lowpass the Hilbert envelope well below the 1/T bit rate to smooth it.

    Cutoff is a fraction of the bit rate, following the same lowpass-below-
    carrier logic used elsewhere in this repo (e.g. WORK_TEN's 300 Hz cutoff
    on a much lower message bandwidth): here the "message" bandwidth is set
    by the bit rate itself, so the cutoff is chosen at 0.3 / T, comfortably
    below 1/T while still tracking bit transitions.
    """
    bit_rate = 1.0 / bit_period_s
    cutoff_hz = 0.3 * bit_rate
    taps = design_fir_lowpass(cutoff_hz, sample_rate, order=50)
    return apply_filter(taps, [1.0], envelope)


def bits_from_envelope(
    smoothed_envelope: np.ndarray,
    sample_rate: float,
    bit_period_s: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Average the smoothed envelope over each bit window and threshold it.

    Threshold: midpoint between the two 1-D k-means (Otsu-style two-cluster)
    centroids of the per-bit averages, which self-calibrates to whatever
    high/low amplitude levels are actually present instead of assuming a
    fixed absolute level.

    Returns `(bits, per_bit_average)`.
    """
    samples_per_bit = int(round(bit_period_s * sample_rate))
    n_bits = len(smoothed_envelope) // samples_per_bit
    per_bit_average = np.array(
        [
            smoothed_envelope[i * samples_per_bit : (i + 1) * samples_per_bit].mean()
            for i in range(n_bits)
        ]
    )

    threshold = _two_cluster_threshold(per_bit_average)
    bits = (per_bit_average > threshold).astype(int)
    return bits, per_bit_average


def _two_cluster_threshold(values: np.ndarray) -> float:
    """1-D 2-means threshold: midpoint between the two converged centroids."""
    low, high = values.min(), values.max()
    if np.isclose(low, high):
        return low
    c_low, c_high = low, high
    for _ in range(50):
        mid = (c_low + c_high) / 2
        group_low = values[values <= mid]
        group_high = values[values > mid]
        if len(group_low) == 0 or len(group_high) == 0:
            break
        new_c_low, new_c_high = group_low.mean(), group_high.mean()
        if np.isclose(new_c_low, c_low) and np.isclose(new_c_high, c_high):
            c_low, c_high = new_c_low, new_c_high
            break
        c_low, c_high = new_c_low, new_c_high
    return (c_low + c_high) / 2


def square_wave_from_bits(bits: np.ndarray, sample_rate: float, bit_period_s: float) -> np.ndarray:
    """Expand per-bit 0/1 values into a sample-rate square wave for plotting."""
    samples_per_bit = int(round(bit_period_s * sample_rate))
    return np.repeat(bits, samples_per_bit).astype(float)
