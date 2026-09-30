"""End-to-end: CSV path -> DecodeResult, wiring data/envelope/symbols/decode."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .data import load_signal
from .decode import bytes_to_text, group_with_dashes, levels_to_bytes
from .envelope import am_envelope
from .symbols import calibrate, levels_from_data_symbols, symbol_averages


@dataclass
class DecodeResult:
    sample_rate_hz: float
    carrier_hz: float
    cutoff_hz: float
    n_symbols_total: int
    n_data_symbols: int
    calibration_slope: float
    calibration_intercept: float
    calibration_max_abs_residual: float
    levels: np.ndarray
    byte_values: list[int]
    terminator_found: bool
    text: str
    text_grouped: str


def decode_csv(csv_path: str | Path, display_block_size: int = 6) -> DecodeResult:
    t, amplitude, fs = load_signal(csv_path)

    # 1) FFT to measure the real carrier, 2) Hilbert for the envelope,
    # 3) lowpass cutoff derived from that measured carrier -- see envelope.py.
    envelope, carrier_hz, cutoff_hz = am_envelope(amplitude, fs)

    avgs = symbol_averages(envelope, fs)

    slope, intercept, residuals = calibrate(avgs)
    levels = levels_from_data_symbols(avgs, slope, intercept)

    byte_values, terminator_found = levels_to_bytes(levels)
    text = bytes_to_text(byte_values)
    text_grouped = group_with_dashes(text, display_block_size)

    return DecodeResult(
        sample_rate_hz=fs,
        carrier_hz=carrier_hz,
        cutoff_hz=cutoff_hz,
        n_symbols_total=len(avgs),
        n_data_symbols=len(levels),
        calibration_slope=slope,
        calibration_intercept=intercept,
        calibration_max_abs_residual=float(np.max(np.abs(residuals))),
        levels=levels,
        byte_values=byte_values,
        terminator_found=terminator_found,
        text=text,
        text_grouped=text_grouped,
    )
