"""Moving-average (boxcar) digital low-pass filter lab."""

from __future__ import annotations

from .audio import load_audio, segment
from .filters import cutoff_to_window, moving_average_by_cutoff, moving_average_filter
from .spectrum import single_sided_fft
from .waveforms import sample_times, sine_am, sine_tone, square_am, square_tone

__all__ = [
    "cutoff_to_window",
    "moving_average_filter",
    "moving_average_by_cutoff",
    "single_sided_fft",
    "sample_times",
    "sine_tone",
    "sine_am",
    "square_tone",
    "square_am",
    "load_audio",
    "segment",
]
