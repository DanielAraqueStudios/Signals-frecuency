"""CSV loading for the AM-modulated signal sample."""

from __future__ import annotations

from pathlib import Path

import numpy as np


def load_am_csv(path: str | Path) -> tuple[np.ndarray, np.ndarray, float]:
    """Load a `<f>_1_modulated_signal_<fc>_<fs>_<T>.csv` sample.

    Returns `(t, x, fs)` where `fs` is measured directly from the timestamp
    column (`1 / dt`), not parsed from the filename.
    """
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    t = data[:, 0]
    x = data[:, 1]
    dt = np.diff(t).mean()
    fs = 1.0 / dt
    return t, x, fs
