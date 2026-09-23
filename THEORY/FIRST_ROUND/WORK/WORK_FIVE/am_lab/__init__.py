"""AM/aliasing FFT demo: sample generation and spectrum computation.

Public API mirrors the split used in `WORK_THREE/signal_lab` and
`WORK_FOUR/conv_lab`: pure math in `signals.py`/`spectrum.py`, `main.py`
only wires them together and plots.
"""

from __future__ import annotations

from .signals import sample_times, modulated_signal, tone_signal
from .spectrum import single_sided_fft

__all__ = [
    "sample_times",
    "modulated_signal",
    "tone_signal",
    "single_sided_fft",
]
