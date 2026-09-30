"""End-to-end round trip: build a synthetic 16-level AM signal for a KNOWN
string, run the full envelope -> symbols -> decode pipeline, and assert the
exact string comes back out. This is the critical correctness test for the
whole package -- if this passes, the pipeline logic is proven correct
independently of any real, possibly-noisy CSV file."""

from __future__ import annotations

import numpy as np

from decode_lab.envelope import am_envelope
from decode_lab.decode import bytes_to_text, levels_to_bytes
from decode_lab.symbols import (
    SYMBOL_DURATION_S,
    calibrate,
    levels_from_data_symbols,
    symbol_averages,
)

CARRIER_HZ = 1000.0
SAMPLE_RATE_HZ = 53730.0


def _build_am_signal(levels: list[int]) -> np.ndarray:
    """16-level AM: amplitude(t) = level * cos(2*pi*f_c*t) over one symbol
    window per level, levels scaled to [0, 15] amplitude units directly
    (matches the real format's apparent amplitude-per-level scaling)."""
    samples_per_symbol = int(round(SYMBOL_DURATION_S * SAMPLE_RATE_HZ))
    chunks = []
    for level in levels:
        t = np.arange(samples_per_symbol) / SAMPLE_RATE_HZ
        chunks.append(level * np.cos(2 * np.pi * CARRIER_HZ * t))
    return np.concatenate(chunks)


def test_known_string_round_trip():
    message = "Hi!"
    byte_values = [ord(c) for c in message]

    calibration_levels = list(range(16))
    data_levels = []
    for b in byte_values:
        data_levels.append((b >> 4) & 0xF)
        data_levels.append(b & 0xF)
    data_levels += [0, 0]  # 0x00 terminator

    all_levels = calibration_levels + data_levels
    signal = _build_am_signal(all_levels)

    envelope, measured_carrier_hz, cutoff_hz = am_envelope(signal, SAMPLE_RATE_HZ)
    assert abs(measured_carrier_hz - CARRIER_HZ) < 5.0
    assert cutoff_hz > 0
    avgs = symbol_averages(envelope, SAMPLE_RATE_HZ)
    slope, intercept, residuals = calibrate(avgs)
    assert np.max(np.abs(residuals)) < 0.5

    recovered_levels = levels_from_data_symbols(avgs, slope, intercept)
    byte_values_out, terminator_found = levels_to_bytes(recovered_levels)
    text = bytes_to_text(byte_values_out)

    assert terminator_found is True
    assert text == message
