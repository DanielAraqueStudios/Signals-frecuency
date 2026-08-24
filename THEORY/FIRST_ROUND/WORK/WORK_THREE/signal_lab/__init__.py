"""Signal sampling and Fourier-series synthesis exercises (items 4-7, 9)."""

from .plotting import (
    plot_fft_comparison,
    plot_sine_sampling_grid,
    plot_square_construction,
    plot_square_sampling_grid,
    plot_triangular_sampling_grid,
)
from .spectral import compute_fft, dominant_frequency, signal_stats
from .waveforms import (
    angular_frequency,
    sample_times,
    sine_wave,
    square_wave_fourier,
    square_wave_ideal,
    triangular_wave,
)

__all__ = [
    "angular_frequency",
    "sample_times",
    "sine_wave",
    "square_wave_fourier",
    "square_wave_ideal",
    "triangular_wave",
    "compute_fft",
    "dominant_frequency",
    "signal_stats",
    "plot_sine_sampling_grid",
    "plot_square_construction",
    "plot_triangular_sampling_grid",
    "plot_square_sampling_grid",
    "plot_fft_comparison",
]
