import numpy as np
import pytest

from avg_filter_lab.filters import cutoff_to_window, moving_average_by_cutoff, moving_average_filter


def test_cutoff_to_window_formula():
    # N = round(0.443 * fs / fc)
    assert cutoff_to_window(cutoff_hz=100, sample_rate=10_000) == round(0.443 * 10_000 / 100)


def test_cutoff_to_window_minimum_is_one():
    assert cutoff_to_window(cutoff_hz=1_000_000, sample_rate=1000) == 1


def test_cutoff_to_window_rejects_nonpositive_cutoff():
    with pytest.raises(ValueError):
        cutoff_to_window(cutoff_hz=0, sample_rate=1000)


def test_moving_average_rejects_window_below_one():
    with pytest.raises(ValueError):
        moving_average_filter(np.array([1.0, 2.0, 3.0]), window=0)


def test_moving_average_preserves_constant_signal():
    signal = np.full(200, 3.5)
    filtered = moving_average_filter(signal, window=10)
    # Away from the edges, a DC signal must pass through unchanged.
    np.testing.assert_allclose(filtered[20:-20], 3.5)


def test_moving_average_output_length_matches_input():
    signal = np.arange(50.0)
    filtered = moving_average_filter(signal, window=7)
    assert filtered.shape == signal.shape


def test_moving_average_attenuates_high_frequency_more_than_low_frequency():
    sample_rate = 10_000
    t = np.arange(0, 1.0, 1 / sample_rate)
    low_tone = np.sin(2 * np.pi * 20 * t)
    high_tone = np.sin(2 * np.pi * 2000 * t)

    filtered_low, window = moving_average_by_cutoff(low_tone, cutoff_hz=100, sample_rate=sample_rate)
    filtered_high, _ = moving_average_by_cutoff(high_tone, cutoff_hz=100, sample_rate=sample_rate)

    margin = window
    low_ratio = np.std(filtered_low[margin:-margin]) / np.std(low_tone[margin:-margin])
    high_ratio = np.std(filtered_high[margin:-margin]) / np.std(high_tone[margin:-margin])

    assert high_ratio < low_ratio
