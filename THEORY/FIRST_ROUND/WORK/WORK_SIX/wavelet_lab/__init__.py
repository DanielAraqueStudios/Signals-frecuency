"""Wavelet spectrum, vector-correlation (Tarea 2 Parte 1) and multi-voice
scalogram helpers for WORK_SIX.
"""

from __future__ import annotations

from .audio import load_audio
from .plotting import plot_correlation_vector, plot_scalogram
from .vectors import VECTORS, correlation_vector_100
from .wavelets import cwt_scalogram

__all__ = [
    "load_audio",
    "VECTORS",
    "correlation_vector_100",
    "cwt_scalogram",
    "plot_scalogram",
    "plot_correlation_vector",
]
