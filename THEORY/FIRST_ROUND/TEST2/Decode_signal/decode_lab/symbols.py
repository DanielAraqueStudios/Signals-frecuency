"""Envelope -> per-symbol average -> calibrated level (0..15).

Signal format (given by the assignment, not inferred):
  - 1000 Hz carrier, 16-level AM (levels 0..15).
  - Each symbol lasts 15 ms.
  - First 240 ms (16 symbols) is a calibration ramp: levels 0,1,2,...,15.
  - Then data: 2 nibbles per character, high nibble first.
  - Terminated by a 0x00 byte.
"""

from __future__ import annotations

import numpy as np

SYMBOL_DURATION_S = 0.015
N_CALIBRATION_SYMBOLS = 16
CALIBRATION_DURATION_S = SYMBOL_DURATION_S * N_CALIBRATION_SYMBOLS  # 240 ms


def symbol_averages(envelope: np.ndarray, sample_rate: float, trim_fraction: float = 0.2) -> np.ndarray:
    """Average each 15 ms symbol window, trimming `trim_fraction` off each
    edge to avoid transition artifacts between adjacent symbols."""
    samples_per_symbol = int(round(SYMBOL_DURATION_S * sample_rate))
    n_symbols = len(envelope) // samples_per_symbol
    trim = int(samples_per_symbol * trim_fraction)

    averages = np.empty(n_symbols)
    for i in range(n_symbols):
        start = i * samples_per_symbol
        end = start + samples_per_symbol
        segment = envelope[start:end]
        averages[i] = segment[trim: len(segment) - trim].mean()
    return averages


def calibrate(symbol_avgs: np.ndarray) -> tuple[float, float, np.ndarray]:
    """Fit `level = slope*avg + intercept` from the first 16 symbols (the
    known 0..15 calibration ramp). Returns (slope, intercept, residuals)."""
    calibration_avgs = symbol_avgs[:N_CALIBRATION_SYMBOLS]
    known_levels = np.arange(N_CALIBRATION_SYMBOLS, dtype=float)
    design = np.vstack([calibration_avgs, np.ones_like(calibration_avgs)]).T
    slope, intercept = np.linalg.lstsq(design, known_levels, rcond=None)[0]
    residuals = (slope * calibration_avgs + intercept) - known_levels
    return float(slope), float(intercept), residuals


def levels_from_data_symbols(symbol_avgs: np.ndarray, slope: float, intercept: float) -> np.ndarray:
    """Apply the calibration fit to the symbols after the calibration ramp,
    rounding to the nearest valid level and clipping to [0, 15]."""
    data_avgs = symbol_avgs[N_CALIBRATION_SYMBOLS:]
    raw = slope * data_avgs + intercept
    return np.clip(np.round(raw), 0, 15).astype(int)
