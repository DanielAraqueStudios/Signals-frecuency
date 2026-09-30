"""CSV loading for the OOK-modulated bitstream signal."""

from __future__ import annotations

import numpy as np


def load_signal(csv_path: str) -> tuple[np.ndarray, np.ndarray, float]:
    """Load `Tiempo (s),Amplitud` CSV, return `(t, amplitude, sample_rate_hz)`.

    Sample rate is derived from the actual timestamps, not assumed from the
    filename.
    """
    data = np.loadtxt(csv_path, delimiter=",", skiprows=1)
    t = data[:, 0]
    amplitude = data[:, 1]
    dt = np.diff(t).mean()
    sample_rate = 1.0 / dt
    return t, amplitude, sample_rate
