"""Item 3 — FFT-based comparison of violin, drum, and cat recordings.

Uses ``scipy.io.wavfile`` (stdlib-adjacent, always available with SciPy)
rather than ``librosa``, since all three source recordings are plain WAV
files and don't need format transcoding or resampling.
"""

from __future__ import annotations

import numpy as np


def load_wav(path: str) -> tuple[int, np.ndarray]:
    """Load a WAV file, downmixing to mono and normalizing to ``[-1, 1]``.

    Returns ``(sample_rate, signal)``.
    """
    from scipy.io import wavfile

    sample_rate, audio = wavfile.read(path)
    if audio.ndim > 1:
        audio = audio[:, 0]
    audio = audio.astype(np.float64)
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak
    return sample_rate, audio


def compute_fft_spectrum(signal: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
    """Single-sided, amplitude-normalized FFT magnitude spectrum.

    Returns ``(frequencies, magnitude)``.
    """
    n = len(signal)
    freqs = np.fft.rfftfreq(n, 1 / sample_rate)
    magnitude = np.abs(np.fft.rfft(signal)) / n
    return freqs, magnitude


def dominant_frequency(freqs: np.ndarray, magnitude: np.ndarray) -> float:
    """Dominant (non-DC) frequency from a precomputed spectrum."""
    if len(magnitude) <= 1:
        return 0.0
    peak_index = np.argmax(magnitude[1:]) + 1
    return float(freqs[peak_index])
