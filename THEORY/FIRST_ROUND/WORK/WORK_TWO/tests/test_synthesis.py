"""Unit tests for fourier_square.synthesis.

Covers pure signal-generation logic. Plotting (`fourier_square.plotting`)
is not tested here since it only arranges Matplotlib figures around
already-tested data.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fourier_square.synthesis import (
    DEFAULT_DURATION_S,
    DEFAULT_FUNDAMENTAL_HZ,
    angular_frequency,
    fourier_square_wave,
    sample_times,
)


class TestAngularFrequency:
    def test_converts_hz_to_rad_per_s(self):
        assert angular_frequency(1.0) == pytest.approx(2 * np.pi)

    def test_default_fundamental_matches_docstring_constant(self):
        # DEFAULT_FUNDAMENTAL_HZ is documented as w0 = 6*pi (k=1) -> 3 Hz.
        assert angular_frequency(DEFAULT_FUNDAMENTAL_HZ) == pytest.approx(6 * np.pi)


class TestSampleTimes:
    def test_sample_count_matches_duration_and_rate(self):
        t = sample_times(duration_s=1.0, sample_rate=1000)
        assert len(t) == 1000

    def test_starts_at_zero_and_is_evenly_spaced(self):
        t = sample_times(duration_s=DEFAULT_DURATION_S, sample_rate=100)
        assert t[0] == 0.0
        assert np.allclose(np.diff(t), 1 / 100)


class TestFourierSquareWave:
    def test_single_harmonic_is_scaled_sine(self):
        w0 = angular_frequency(DEFAULT_FUNDAMENTAL_HZ)
        t = sample_times(DEFAULT_DURATION_S, sample_rate=1000)

        f_t = fourier_square_wave(t, w0, num_harmonics=1)

        assert np.allclose(f_t, (4 / np.pi) * np.sin(w0 * t))

    def test_output_shape_matches_input(self):
        w0 = angular_frequency(DEFAULT_FUNDAMENTAL_HZ)
        t = sample_times(DEFAULT_DURATION_S, sample_rate=500)

        f_t = fourier_square_wave(t, w0, num_harmonics=5)

        assert f_t.shape == t.shape

    def test_rejects_fewer_than_one_harmonic(self):
        w0 = angular_frequency(DEFAULT_FUNDAMENTAL_HZ)
        t = sample_times(DEFAULT_DURATION_S, sample_rate=100)

        with pytest.raises(ValueError):
            fourier_square_wave(t, w0, num_harmonics=0)

    def test_more_harmonics_converge_toward_unit_amplitude(self):
        # Away from the wave's discontinuities (t=0, T/2, T, ...), the
        # partial sums converge to the ideal square wave's +/-1 plateau.
        # At t = T/4 the ideal value is +1.
        w0 = angular_frequency(DEFAULT_FUNDAMENTAL_HZ)
        period = 2 * np.pi / w0
        t = np.array([period / 4])

        error_few = abs(1.0 - fourier_square_wave(t, w0, num_harmonics=1)[0])
        error_many = abs(1.0 - fourier_square_wave(t, w0, num_harmonics=50)[0])

        assert error_many < error_few
        assert error_many < 0.05

    def test_half_period_shift_is_antisymmetric(self):
        # A square wave built only from odd harmonics satisfies
        # f(t + T/2) = -f(t).
        w0 = angular_frequency(DEFAULT_FUNDAMENTAL_HZ)
        period = 2 * np.pi / w0
        t = sample_times(period / 2, sample_rate=1000)

        f_t = fourier_square_wave(t, w0, num_harmonics=10)
        f_t_shifted = fourier_square_wave(t + period / 2, w0, num_harmonics=10)

        assert np.allclose(f_t_shifted, -f_t, atol=1e-9)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
