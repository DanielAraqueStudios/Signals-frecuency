import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signal_tools.sampling import sine_wave, sample_signal, quantize_dac, is_aliased


class TestSineWave:
    def test_zero_at_origin(self):
        t = np.array([0.0])
        assert sine_wave(100.0, t)[0] == 0.0

    def test_amplitude_scales_peak(self):
        t = np.linspace(0, 1 / 100.0, 1000)
        wave = sine_wave(100.0, t, amplitude=2.5)
        assert np.isclose(np.max(wave), 2.5, atol=0.01)


class TestSampleSignal:
    def test_sample_count_matches_rate_and_duration(self):
        t_samples, values = sample_signal(100.0, 1000.0, 0.05)
        assert len(t_samples) == 50
        assert len(values) == 50

    def test_low_rate_produces_few_samples(self):
        t_samples, _ = sample_signal(100.0, 70.0, 0.05)
        assert len(t_samples) == 4


class TestQuantizeDac:
    def test_output_bounded(self):
        signal = np.linspace(-1, 1, 100)
        quantized = quantize_dac(signal, bits=3)
        assert np.all(quantized >= -1.0) and np.all(quantized <= 1.0)

    def test_number_of_distinct_levels(self):
        signal = np.linspace(-1, 1, 1000)
        quantized = quantize_dac(signal, bits=3)
        assert len(np.unique(quantized)) <= 2**3

    def test_more_bits_gives_finer_resolution(self):
        signal = np.linspace(-1, 1, 1000)
        coarse = quantize_dac(signal, bits=1)
        fine = quantize_dac(signal, bits=6)
        assert len(np.unique(fine)) > len(np.unique(coarse))

    def test_raises_on_invalid_bits(self):
        try:
            quantize_dac(np.array([0.0]), bits=0)
            assert False, "expected ValueError"
        except ValueError:
            pass


class TestIsAliased:
    def test_below_nyquist_is_aliased(self):
        assert is_aliased(signal_frequency_hz=100.0, sample_rate_hz=70.0) is True

    def test_above_nyquist_is_not_aliased(self):
        assert is_aliased(signal_frequency_hz=100.0, sample_rate_hz=500.0) is False
        assert is_aliased(signal_frequency_hz=100.0, sample_rate_hz=1000.0) is False

    def test_exactly_at_nyquist_is_not_aliased(self):
        assert is_aliased(signal_frequency_hz=100.0, sample_rate_hz=200.0) is False
