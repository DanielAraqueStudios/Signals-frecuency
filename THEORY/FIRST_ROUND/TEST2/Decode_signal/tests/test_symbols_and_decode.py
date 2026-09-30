"""Unit tests: calibration fit, level rounding, nibble/byte decode -- all
deterministic, no CSV file required."""

from __future__ import annotations

import numpy as np

from decode_lab.decode import bytes_to_text, group_with_dashes, levels_to_bytes
from decode_lab.symbols import calibrate, levels_from_data_symbols


def test_calibrate_recovers_exact_linear_map():
    # avg = 2*level + 5, noiseless
    avgs = 2.0 * np.arange(16) + 5.0
    slope, intercept, residuals = calibrate(avgs)
    assert slope == 0.5 or abs(slope - 0.5) < 1e-9
    assert abs(intercept - (-2.5)) < 1e-9
    assert np.allclose(residuals, 0.0, atol=1e-9)


def test_calibrate_handles_noisy_ramp():
    rng = np.random.default_rng(0)
    avgs = 2.0 * np.arange(16) + 5.0 + rng.normal(0, 0.05, 16)
    slope, intercept, residuals = calibrate(avgs)
    assert abs(slope - 0.5) < 0.05
    assert np.max(np.abs(residuals)) < 0.5


def test_levels_from_data_symbols_rounds_and_clips():
    # calibration symbols (16) + 4 data symbols
    calib = 2.0 * np.arange(16) + 5.0
    data = np.array([5.0, 45.0, -100.0, 1000.0])  # -> levels far below/above range
    all_avgs = np.concatenate([calib, data])
    slope, intercept, _ = calibrate(all_avgs[:16])
    levels = levels_from_data_symbols(all_avgs, slope, intercept)
    assert len(levels) == 4
    assert levels[0] == 0  # (5-5)/2 = 0
    assert levels[1] == 15  # clipped from 20
    assert levels[2] == 0  # clipped from negative
    assert levels[3] == 15  # clipped from way above 15


def test_levels_to_bytes_stops_at_terminator():
    # 'A' = 0x41 -> nibbles (4,1); 'B' = 0x42 -> (4,2); then terminator (0,0)
    levels = np.array([4, 1, 4, 2, 0, 0, 9, 9])
    byte_values, terminator_found = levels_to_bytes(levels)
    assert byte_values == [0x41, 0x42]
    assert terminator_found is True


def test_levels_to_bytes_reports_missing_terminator():
    levels = np.array([4, 1, 4, 2])  # 'A', 'B', no terminator
    byte_values, terminator_found = levels_to_bytes(levels)
    assert byte_values == [0x41, 0x42]
    assert terminator_found is False


def test_bytes_to_text_round_trip_known_string():
    known = "Hi!"
    byte_values = [ord(c) for c in known]
    assert bytes_to_text(byte_values) == known


def test_bytes_to_text_escapes_non_printable():
    text = bytes_to_text([0x01, 0x7f])
    assert text == "\\x01\\x7f"


def test_group_with_dashes_splits_into_equal_blocks():
    assert group_with_dashes("XLmtZhX0r0RKzndPKPVQg0dqiNJnSv", 6) == (
        "XLmtZh-X0r0RK-zndPKP-VQg0dq-iNJnSv"
    )


def test_group_with_dashes_handles_remainder_block():
    # 7 chars, block size 3 -> two full blocks + one 1-char remainder block
    assert group_with_dashes("ABCDEFG", 3) == "ABC-DEF-G"


def test_group_with_dashes_empty_string():
    assert group_with_dashes("", 6) == ""
