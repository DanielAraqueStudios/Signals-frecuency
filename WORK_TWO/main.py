"""CLI entry point: plot Fourier-series square-wave reconstructions across
several sampling rates, illustrating Gibbs phenomenon and sample density.

Usage:
    python main.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from fourier_square import (
    DEFAULT_DURATION_S,
    DEFAULT_FUNDAMENTAL_HZ,
    angular_frequency,
    plot_sampling_rate_grid,
)

# Number of odd harmonics to reconstruct, one subplot per value.
HARMONICS_LIST = [1, 2, 3, 5, 10]

# Sampling rates (Hz) to compare, one figure per value.
SAMPLING_RATES = [1000, 2000, 3000, 6000, 30000]


def main() -> None:
    """Render one comparison figure per configured sampling rate."""
    w0 = angular_frequency(DEFAULT_FUNDAMENTAL_HZ)
    for sample_rate in SAMPLING_RATES:
        plot_sampling_rate_grid(w0, DEFAULT_DURATION_S, HARMONICS_LIST, sample_rate)
    plt.show()


if __name__ == "__main__":
    main()
