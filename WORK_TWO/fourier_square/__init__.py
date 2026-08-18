"""Fourier-series synthesis and visualization of a band-limited square wave."""

from .plotting import plot_sampling_rate_grid
from .synthesis import (
    DEFAULT_DURATION_S,
    DEFAULT_FUNDAMENTAL_HZ,
    angular_frequency,
    fourier_square_wave,
    sample_times,
)

__all__ = [
    "DEFAULT_FUNDAMENTAL_HZ",
    "DEFAULT_DURATION_S",
    "angular_frequency",
    "fourier_square_wave",
    "sample_times",
    "plot_sampling_rate_grid",
]
