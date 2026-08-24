"""Animal-sound spectral/statistical analyzer (item 8): core logic + GUI."""

from .core import (
    ANALYSIS_WINDOW_S,
    analysis_window,
    analyze_audio,
    compare_categories,
    load_audio,
    separability_score,
)

__all__ = [
    "ANALYSIS_WINDOW_S",
    "load_audio",
    "analysis_window",
    "analyze_audio",
    "separability_score",
    "compare_categories",
]
