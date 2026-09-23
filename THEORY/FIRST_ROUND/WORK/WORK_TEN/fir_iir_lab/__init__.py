"""FIR/IIR filtering + Hilbert-envelope lab: sample generation, spectral
tools, filter design, and AM cat-audio modulation.

Public API mirrors the split used in `WORK_THREE/signal_lab`, `WORK_FOUR/
conv_lab` and `WORK_FIVE/am_lab`: pure math per module, `main.py` only wires
them together and plots.
"""

from __future__ import annotations

from .signals import sample_times, tone_signal, am_modulate
from .spectrum import single_sided_fft, remove_negative_frequencies
from .filters import design_fir_lowpass, design_iir_lowpass, apply_filter
from .hilbert_tools import hilbert_envelope
from .audio import load_audio

__all__ = [
    "sample_times",
    "tone_signal",
    "am_modulate",
    "single_sided_fft",
    "remove_negative_frequencies",
    "design_fir_lowpass",
    "design_iir_lowpass",
    "apply_filter",
    "hilbert_envelope",
    "load_audio",
]
