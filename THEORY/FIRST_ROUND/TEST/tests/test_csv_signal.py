import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signal_tools.csv_signal import (
    load_csv_signal,
    segment_signal,
    dominant_frequency,
    SAMPLE_RATE_HZ,
    SEGMENT_DURATION_S,
)

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Muestra01.csv")


class TestLoadCsvSignal:
    def test_loads_correct_length(self):
        signal = load_csv_signal(CSV_PATH)
        assert len(signal) == 1000

    def test_returns_ndarray(self):
        signal = load_csv_signal(CSV_PATH)
        assert isinstance(signal, np.ndarray)


class TestSegmentSignal:
    def test_default_params_give_four_segments(self):
        signal = load_csv_signal(CSV_PATH)
        segments = segment_signal(signal)
        assert len(segments) == 4
        for seg in segments:
            assert len(seg) == 250

    def test_drops_incomplete_trailing_segment(self):
        signal = np.arange(260)
        segments = segment_signal(signal, sample_rate=5000.0, segment_duration_s=0.05)
        assert len(segments) == 1
        assert len(segments[0]) == 250

    def test_raises_on_zero_samples_per_segment(self):
        signal = np.arange(10)
        try:
            segment_signal(signal, sample_rate=1.0, segment_duration_s=0.0001)
            assert False, "expected ValueError"
        except ValueError:
            pass


class TestDominantFrequency:
    def test_pure_tone_recovered(self):
        fs = 5000.0
        t = np.arange(250) / fs
        signal = np.sin(2 * np.pi * 500 * t)
        assert abs(dominant_frequency(signal, fs) - 500) < 25

    def test_empty_after_dc_only_returns_zero(self):
        signal = np.zeros(1)
        assert dominant_frequency(signal, 5000.0) == 0.0

    def test_real_csv_segments_have_plausible_frequencies(self):
        signal = load_csv_signal(CSV_PATH)
        segments = segment_signal(signal)
        for seg in segments:
            freq = dominant_frequency(seg, SAMPLE_RATE_HZ)
            assert 0 <= freq <= SAMPLE_RATE_HZ / 2
