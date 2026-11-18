"""NLMS adaptive filter lab: system identification, noise cancellation, and a
non-stationary-power comparison against plain LMS."""

from .audio import load_audio
from .noise import add_noise
from .signals import sample_times, tone_signal, varying_power_signal
from .adaptive import lms_filter, nlms_filter

__all__ = [
    "load_audio",
    "add_noise",
    "sample_times",
    "tone_signal",
    "varying_power_signal",
    "lms_filter",
    "nlms_filter",
]
