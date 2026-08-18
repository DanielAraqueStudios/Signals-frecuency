"""Unit tests for animal_analyzer.core.

`load_audio` (file I/O via librosa) is intentionally excluded — it needs
real audio files on disk. See `readme.md` for how to supply them under
`audio_samples/`.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from animal_analyzer.core import analysis_window, analyze_audio, compare_categories, separability_score
from signal_lab.waveforms import sample_times, sine_wave


class TestAnalysisWindow:
    def test_truncates_to_window_length(self):
        signal = np.arange(1000)
        windowed = analysis_window(signal, sample_rate=100, window_s=3.0)
        assert len(windowed) == 300

    def test_shorter_signal_is_returned_whole(self):
        signal = np.arange(50)
        windowed = analysis_window(signal, sample_rate=100, window_s=3.0)
        assert len(windowed) == 50


class TestAnalyzeAudio:
    def test_recovers_known_tone_and_stats(self):
        t = sample_times(5.0, sample_rate=8000)  # 5s signal, only first 3s analyzed
        signal = sine_wave(t, frequency_hz=440.0, amplitude=2.0)

        result = analyze_audio(signal, sample_rate=8000)

        assert len(result["windowed_signal"]) == 3 * 8000
        assert result["dominant_frequency_hz"] == pytest.approx(440.0, abs=2.0)
        assert result["mean"] == pytest.approx(0.0, abs=1e-6)
        assert result["std"] > 0


class TestSeparabilityScore:
    def test_identical_results_are_not_separable(self):
        t = sample_times(3.0, sample_rate=8000)
        signal = sine_wave(t, frequency_hz=200.0)
        result = analyze_audio(signal, sample_rate=8000)

        assert separability_score(result, result) == 0.0

    def test_farther_apart_tones_score_higher(self):
        t = sample_times(3.0, sample_rate=8000)
        low = analyze_audio(sine_wave(t, frequency_hz=200.0), sample_rate=8000)
        mid = analyze_audio(sine_wave(t, frequency_hz=400.0), sample_rate=8000)
        high = analyze_audio(sine_wave(t, frequency_hz=2000.0), sample_rate=8000)

        assert separability_score(low, high) > separability_score(low, mid)


class TestCompareCategories:
    def test_report_mentions_every_category_and_pair(self):
        t = sample_times(3.0, sample_rate=8000)
        results = {
            "Gato": analyze_audio(sine_wave(t, frequency_hz=1200.0), sample_rate=8000),
            "Perro": analyze_audio(sine_wave(t, frequency_hz=300.0), sample_rate=8000),
        }

        report = compare_categories(results)

        assert "Gato" in report
        assert "Perro" in report
        assert "Gato vs Perro" in report


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
