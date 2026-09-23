"""Manual (hand-derived) IIR filter design + application, vs. a `scipy`
reference, for the 2nd-order (item A) and 4th-order (item B) Butterworth
low-pass exercises.
"""

from __future__ import annotations

from .apply import apply_cascade, apply_difference_equation
from .coefficients import (
    SQRT2,
    biquad_butterworth_bilinear,
    combine_sections,
    order4_manual_sections,
)
from .reference import scipy_butter_lowpass
from .signals import generate_test_signal

__all__ = [
    "SQRT2",
    "apply_cascade",
    "apply_difference_equation",
    "biquad_butterworth_bilinear",
    "combine_sections",
    "order4_manual_sections",
    "scipy_butter_lowpass",
    "generate_test_signal",
]
