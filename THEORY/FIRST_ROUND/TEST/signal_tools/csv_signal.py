"""Item 1 - load and analyze the recorded ``Muestra01.csv`` signal.

The file holds one sample value per line, sampled at ``fs = 5000 Hz``. The
assignment further splits the recording into fixed-duration segments
(``dt = 0.05 s`` -> 250 samples/segment at 5000 Hz) and asks for the dominant
frequency of each segment.
"""

from __future__ import annotations

import numpy as np

SAMPLE_RATE_HZ = 5000.0
SEGMENT_DURATION_S = 0.05


def load_csv_signal(path: str) -> np.ndarray:
    """Load a single-column CSV of sample values into a 1-D array."""
    return np.loadtxt(path, delimiter=",")


def segment_signal(
    signal: np.ndarray,
    sample_rate: float = SAMPLE_RATE_HZ,
    segment_duration_s: float = SEGMENT_DURATION_S,
) -> list[np.ndarray]:
    """Split ``signal`` into consecutive, non-overlapping fixed-size segments.

    Any trailing samples that don't fill a full segment are dropped, matching
    the original script's behavior (``len(signal) // n_samples`` segments).
    """
    n_samples = int(round(sample_rate * segment_duration_s))
    if n_samples < 1:
        raise ValueError("segment_duration_s * sample_rate must be >= 1 sample")
    n_segments = len(signal) // n_samples
    return [signal[i * n_samples : (i + 1) * n_samples] for i in range(n_segments)]


def dominant_frequency(segment: np.ndarray, sample_rate: float = SAMPLE_RATE_HZ) -> float:
    """Return the dominant (non-DC) frequency of a segment via FFT."""
    freqs = np.fft.rfftfreq(len(segment), 1 / sample_rate)
    magnitude = np.abs(np.fft.rfft(segment)) / len(segment)
    if len(magnitude) <= 1:
        return 0.0
    peak_index = np.argmax(magnitude[1:]) + 1  # skip DC bin
    return float(freqs[peak_index])
