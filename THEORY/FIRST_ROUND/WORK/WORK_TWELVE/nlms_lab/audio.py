"""Audio loading for the adaptive-noise-cancellation exercise.

Mirrors `WORK_TEN/fir_iir_lab/audio.py`: `librosa` is imported lazily so the
rest of the package/tests stay importable without it installed.
"""

from __future__ import annotations

import numpy as np


def load_audio(path: str) -> tuple[np.ndarray, int]:
    """Load a mono audio file at its native sample rate.

    Returns:
        `(signal, sample_rate)`.
    """
    import librosa

    signal, sample_rate = librosa.load(path, sr=None, mono=True)
    return signal, sample_rate
