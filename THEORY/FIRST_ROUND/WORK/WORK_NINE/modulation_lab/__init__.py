"""Tarea 5: AM-modulates the 'gato' recording, resampled to 50 kHz and 500 kHz."""

from __future__ import annotations

from .audio import load_audio
from .modulation import CARRIER_FREQ_HZ, LOWPASS_CUTOFF_HZ, am_modulate, lowpass_fft, modulate_at_rate
from .plotting import plot_modulation

__all__ = [
    "load_audio",
    "am_modulate",
    "lowpass_fft",
    "modulate_at_rate",
    "plot_modulation",
    "CARRIER_FREQ_HZ",
    "LOWPASS_CUTOFF_HZ",
]
