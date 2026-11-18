import numpy as np

from nlms_lab.signals import sample_times, tone_signal, varying_power_signal


def test_sample_times_length_and_range():
    t = sample_times(0.1, 1000)
    assert t.size == 100
    assert t[0] == 0
    assert t[-1] < 0.1


def test_tone_signal_matches_closed_form():
    t = np.array([0.0, 0.25, 0.5])
    y = tone_signal(t, frequency_hz=1.0, amplitude=2.0)
    expected = 2.0 * np.sin(2 * np.pi * 1.0 * t)
    assert np.allclose(y, expected)


def test_varying_power_signal_has_distinct_segment_variance():
    rng = np.random.default_rng(0)
    x = varying_power_signal(4000, low_amplitude=0.1, high_amplitude=5.0, rng=rng)
    low_half, high_half = x[:2000], x[2000:]
    assert np.std(high_half) > 10 * np.std(low_half)
