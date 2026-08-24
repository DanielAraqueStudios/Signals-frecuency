"""CLI entry point: renders the item 4-7 and item 9 sampling/synthesis exercises.

Items 1-3 (MATLAB-to-Python port, "melodías", theoretical homework) and
item 8 (audio statistics GUI) are not part of this script — see
`readme.md` and `run_animal_gui.py` respectively.

Usage:
    python main.py
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from signal_lab import (
    angular_frequency,
    plot_fft_comparison,
    plot_sine_sampling_grid,
    plot_square_construction,
    plot_square_sampling_grid,
    plot_triangular_sampling_grid,
)

# --- Item 4: sine sampling -------------------------------------------------
SINE_FREQUENCY_HZ = 3_000
SINE_SAMPLE_RATES_HZ = [1_000, 3_000, 6_000, 30_000, 10_000]
SINE_DURATION_S = 0.005

# --- Item 5: square-wave construction by harmonic count --------------------
SQUARE_FUNDAMENTAL_HZ = 100
CONSTRUCTION_HARMONICS = [1, 2, 5, 10]
CONSTRUCTION_DURATION_S = 0.03

# --- Item 6: triangular-wave sampling ---------------------------------------
TRIANGLE_FREQUENCY_HZ = 10_000
TRIANGLE_V_MAX = 7.0
TRIANGLE_V_MIN = 2.0  # Note: assignment also states "amplitude 9" (Vmax-Vmin=5); Vmax/Vmin are authoritative here.
TRIANGLE_FIXED_RATES_HZ = [30_000, 50_000, 100_000]
TRIANGLE_DURATION_S = 0.0005
_RNG = np.random.default_rng(seed=42)  # fixed seed -> reproducible "random" sample rate
TRIANGLE_RANDOM_RATE_HZ = float(_RNG.integers(20_000, 200_000))  # above Nyquist (20 kHz), below fixed rates' ceiling

# --- Item 7: square-wave sampling (harmonics x sampling rate) --------------
SAMPLING_HARMONICS = [1, 2, 3, 5, 10]
SAMPLING_RATES_HZ = [1_000, 3_000, 6_000, 30_000, 10_000]

# --- Item 9: ideal vs. 10-harmonic FFT comparison ---------------------------
COMPARISON_FREQUENCY_HZ = 100
COMPARISON_SAMPLE_RATE_HZ = 50_000
COMPARISON_HARMONICS = 10
COMPARISON_DURATION_S = 0.03


def main() -> None:
    """Render every configured exercise figure."""
    # Item 4
    plot_sine_sampling_grid(SINE_FREQUENCY_HZ, SINE_DURATION_S, SINE_SAMPLE_RATES_HZ)

    # Item 5
    w0_square = angular_frequency(SQUARE_FUNDAMENTAL_HZ)
    plot_square_construction(w0_square, CONSTRUCTION_DURATION_S, CONSTRUCTION_HARMONICS)

    # Item 6
    triangle_rates = TRIANGLE_FIXED_RATES_HZ + [TRIANGLE_RANDOM_RATE_HZ]
    plot_triangular_sampling_grid(
        TRIANGLE_FREQUENCY_HZ, TRIANGLE_DURATION_S, TRIANGLE_V_MAX, TRIANGLE_V_MIN, triangle_rates
    )

    # Item 7
    for rate in SAMPLING_RATES_HZ:
        plot_square_sampling_grid(w0_square, CONSTRUCTION_DURATION_S, SAMPLING_HARMONICS, rate)

    # Item 9
    plot_fft_comparison(COMPARISON_FREQUENCY_HZ, COMPARISON_DURATION_S, COMPARISON_SAMPLE_RATE_HZ, COMPARISON_HARMONICS)

    plt.show()


if __name__ == "__main__":
    main()
