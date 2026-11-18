"""Synthetic additive noise for the adaptive-noise-cancellation exercise."""

from __future__ import annotations

import numpy as np


def add_noise(signal: np.ndarray, noise_amplitude: float, rng: np.random.Generator) -> np.ndarray:
    """Adds zero-mean white Gaussian noise of the given amplitude (std) to `signal`."""
    return signal + noise_amplitude * rng.standard_normal(signal.shape)
