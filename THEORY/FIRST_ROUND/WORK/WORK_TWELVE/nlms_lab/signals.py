"""Signal generation: time axes, tones, and a non-stationary-power test input."""

from __future__ import annotations

import numpy as np


def sample_times(duration_s: float, sample_rate: float) -> np.ndarray:
    """Builds a `[0, duration_s)` time axis at `sample_rate` samples/second."""
    n_samples = int(sample_rate * duration_s)
    return np.linspace(0, duration_s, n_samples, endpoint=False)


def tone_signal(t: np.ndarray, frequency_hz: float, amplitude: float = 1.0) -> np.ndarray:
    """Pure sine, `amplitude * sin(2*pi*frequency_hz*t)`."""
    return amplitude * np.sin(2 * np.pi * frequency_hz * t)


def varying_power_signal(
    n_samples: int, low_amplitude: float, high_amplitude: float, rng: np.random.Generator
) -> np.ndarray:
    """White-noise input whose amplitude steps from `low_amplitude` to
    `high_amplitude` halfway through -- the non-stationary-power scenario
    used to contrast NLMS's self-scaling step size against plain LMS's fixed
    one (readme.md, "Signal Processing Notes").
    """
    half = n_samples // 2
    low_segment = low_amplitude * rng.standard_normal(half)
    high_segment = high_amplitude * rng.standard_normal(n_samples - half)
    return np.concatenate([low_segment, high_segment])
