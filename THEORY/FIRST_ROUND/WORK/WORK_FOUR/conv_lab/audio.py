"""Audio loading for the convolution exercises.

Mirrors `WORK_THREE/animal_analyzer/core.py::load_audio`: `librosa` is
imported lazily so `kernels.py`/`convolution.py` and their tests stay
importable without it installed.
"""

from __future__ import annotations

import numpy as np


def load_audio(path: str) -> tuple[np.ndarray, int]:
    """Load a mono audio file at its native sample rate.

    Args:
        path: Path to a `.wav`/`.mp3`/`.flac`/`.ogg`/`.m4a` file.

    Returns:
        `(signal, sample_rate)`.
    """
    import librosa

    signal, sample_rate = librosa.load(path, sr=None, mono=True)
    return signal, sample_rate


def segment(signal: np.ndarray, sample_rate: int, duration_s: float, start_s: float = 0.0) -> np.ndarray:
    """Cut a short window out of a signal, for plots dense enough to read.

    A convolution plotted over a full recording (hundreds of thousands of
    samples) is unreadable as individual points/lines; the figures use a
    short segment instead, while the full-length signal is still what
    gets filtered and (optionally) saved.

    Args:
        signal: Full audio signal.
        sample_rate: Samples per second (Hz).
        duration_s: Length of the segment to keep, in seconds.
        start_s: Offset from the start of `signal`, in seconds.

    Returns:
        `signal[start_sample:start_sample + n_samples]` (shorter if the
        signal doesn't extend that far).
    """
    start_sample = int(start_s * sample_rate)
    n_samples = int(duration_s * sample_rate)
    return signal[start_sample:start_sample + n_samples]
