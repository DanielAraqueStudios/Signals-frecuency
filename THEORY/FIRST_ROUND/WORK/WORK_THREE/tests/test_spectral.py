"""Unit tests for signal_lab.spectral."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signal_lab.spectral import compute_fft, dominant_frequency, signal_stats
from signal_lab.waveforms import sample_times, sine_wave


class TestComputeFft:
    def test_rejects_empty_signal(self):
        with pytest.raises(ValueError):
            compute_fft(np.array([]), sample_rate=1000)

    def test_recovers_known_sine_amplitude(self):
        t = sample_times(1.0, sample_rate=2000)
        signal = sine_wave(t, frequency_hz=50.0, amplitude=3.0)

        freqs, magnitude = compute_fft(signal, sample_rate=2000)

        peak_index = np.argmax(magnitude[1:]) + 1
        assert freqs[peak_index] == pytest.approx(50.0, abs=1.0)
        assert magnitude[peak_index] == pytest.approx(3.0, abs=0.05)


class TestDominantFrequency:
    def test_ignores_dc_component(self):
        t = sample_times(1.0, sample_rate=1000)
        signal = 10.0 + sine_wave(t, frequency_hz=40.0, amplitude=1.0)

        freqs, magnitude = compute_fft(signal, sample_rate=1000)

        assert dominant_frequency(freqs, magnitude) == pytest.approx(40.0, abs=1.0)

    def test_single_bin_falls_back_to_it(self):
        assert dominant_frequency(np.array([0.0]), np.array([5.0])) == 0.0


class TestSignalStats:
    def test_matches_numpy_directly(self):
        signal = np.array([1.0, 2.0, 3.0, 4.0])
        stats = signal_stats(signal)
        assert stats["mean"] == pytest.approx(2.5)
        assert stats["std"] == pytest.approx(np.std(signal))

    def test_constant_signal_has_zero_std(self):
        stats = signal_stats(np.full(100, 7.0))
        assert stats["mean"] == pytest.approx(7.0)
        assert stats["std"] == pytest.approx(0.0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
