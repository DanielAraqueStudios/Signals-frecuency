"""Unit tests for signal_lab.waveforms."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signal_lab.waveforms import (
    angular_frequency,
    sample_times,
    sine_wave,
    square_wave_fourier,
    square_wave_ideal,
    triangular_wave,
)


class TestAngularFrequency:
    def test_converts_hz_to_rad_per_s(self):
        assert angular_frequency(1.0) == pytest.approx(2 * np.pi)


class TestSampleTimes:
    def test_sample_count_matches_duration_and_rate(self):
        t = sample_times(duration_s=1.0, sample_rate=1000)
        assert len(t) == 1000

    def test_starts_at_zero_and_is_evenly_spaced(self):
        t = sample_times(duration_s=1.0, sample_rate=100)
        assert t[0] == 0.0
        assert np.allclose(np.diff(t), 1 / 100)


class TestSineWave:
    def test_matches_closed_form(self):
        t = sample_times(1.0, 1000)
        assert np.allclose(sine_wave(t, 3.0, amplitude=2.0), 2.0 * np.sin(2 * np.pi * 3.0 * t))

    def test_default_amplitude_is_unit(self):
        t = np.array([0.25])  # quarter period of a 1 Hz sine -> sin(pi/2) = 1
        assert sine_wave(t, 1.0)[0] == pytest.approx(1.0)


class TestSquareWaveFourier:
    def test_single_harmonic_is_scaled_sine(self):
        w0 = angular_frequency(3.0)
        t = sample_times(1.0, sample_rate=1000)

        f_t = square_wave_fourier(t, w0, num_harmonics=1)

        assert np.allclose(f_t, (4 / np.pi) * np.sin(w0 * t))

    def test_output_shape_matches_input(self):
        w0 = angular_frequency(3.0)
        t = sample_times(1.0, sample_rate=500)

        f_t = square_wave_fourier(t, w0, num_harmonics=5)

        assert f_t.shape == t.shape

    def test_rejects_fewer_than_one_harmonic(self):
        w0 = angular_frequency(3.0)
        t = sample_times(1.0, sample_rate=100)

        with pytest.raises(ValueError):
            square_wave_fourier(t, w0, num_harmonics=0)

    def test_more_harmonics_converge_toward_amplitude_plateau(self):
        w0 = angular_frequency(3.0)
        period = 2 * np.pi / w0
        t = np.array([period / 4])  # ideal square wave value here is +amplitude

        error_few = abs(1.0 - square_wave_fourier(t, w0, num_harmonics=1)[0])
        error_many = abs(1.0 - square_wave_fourier(t, w0, num_harmonics=50)[0])

        assert error_many < error_few
        assert error_many < 0.05

    def test_amplitude_scales_output(self):
        w0 = angular_frequency(3.0)
        t = sample_times(1.0, sample_rate=1000)

        unit = square_wave_fourier(t, w0, num_harmonics=10)
        scaled = square_wave_fourier(t, w0, num_harmonics=10, amplitude=5.0)

        assert np.allclose(scaled, 5.0 * unit)


class TestSquareWaveIdeal:
    def test_plateaus_at_plus_and_minus_amplitude(self):
        t = np.array([0.1, 0.6])  # well inside each half-period of a 1 Hz wave
        values = square_wave_ideal(t, frequency_hz=1.0, amplitude=3.0)
        assert set(np.sign(values)) <= {1.0, -1.0}
        assert np.all(np.abs(values) == pytest.approx(3.0))


class TestTriangularWave:
    def test_stays_within_vmin_vmax(self):
        t = sample_times(1.0, sample_rate=5000)
        wave = triangular_wave(t, frequency_hz=10.0, v_max=7.0, v_min=2.0)
        assert wave.max() <= 7.0 + 1e-9
        assert wave.min() >= 2.0 - 1e-9

    def test_reaches_both_extremes(self):
        t = sample_times(1.0, sample_rate=5000)
        wave = triangular_wave(t, frequency_hz=10.0, v_max=7.0, v_min=2.0)
        assert wave.max() == pytest.approx(7.0, abs=1e-2)
        assert wave.min() == pytest.approx(2.0, abs=1e-2)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
