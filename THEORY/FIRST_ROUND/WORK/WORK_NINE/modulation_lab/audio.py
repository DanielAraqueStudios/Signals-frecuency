"""Audio loading for the modulation exercise.

Mirrors `WORK_THREE/animal_analyzer/core.py::load_audio` and
`WORK_FOUR/conv_lab/audio.py::load_audio`: `librosa` is imported lazily so
`modulation.py` and its tests stay importable without it installed.
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
