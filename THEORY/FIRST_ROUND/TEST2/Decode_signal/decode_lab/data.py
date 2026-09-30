"""CSV loading for the 16-level AM data signals."""

from __future__ import annotations

from pathlib import Path

import numpy as np


def load_signal(csv_path: str | Path) -> tuple[np.ndarray, np.ndarray, float]:
    """Load a `tiempo,amplitud` CSV. Returns (t, amplitude, sample_rate_hz).

    The sample rate is recovered from the real timestamps (median dt), not
    assumed, since these files carry no filename-encoded parameters.
    """
    # np.loadtxt is much faster than np.genfromtxt on large CSVs (some of
    # these files are 60,000+ rows) -- genfromtxt's per-line dtype-sniffing
    # made this take long enough to look like a hang.
    data = np.loadtxt(csv_path, delimiter=",", skiprows=1)
    t = data[:, 0]
    amplitude = data[:, 1]
    dt = float(np.median(np.diff(t)))
    fs = 1.0 / dt
    return t, amplitude, fs
