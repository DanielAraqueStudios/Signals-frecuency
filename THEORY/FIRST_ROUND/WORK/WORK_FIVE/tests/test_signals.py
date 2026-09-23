import numpy as np

from am_lab.signals import modulated_signal, sample_times, tone_signal


def test_sample_times_count():
    t = sample_times(0.05, 10**5)
    assert t.size == int(10**5 * 0.05)


def test_sample_times_starts_at_zero_and_excludes_endpoint():
    t = sample_times(1.0, 10)
    assert t[0] == 0.0
    assert t.size == 10


def test_tone_signal_matches_closed_form():
    t = sample_times(0.01, 1000)
    expected = np.sin(2 * np.pi * 60 * t)
    np.testing.assert_allclose(tone_signal(t, 60), expected)


def test_modulated_signal_matches_closed_form():
    t = sample_times(0.01, 1000)
    expected = (2 + np.sin(2 * np.pi * 60 * t)) * np.sin(2 * np.pi * 100 * t)
    np.testing.assert_allclose(modulated_signal(t, 60, 100), expected)


def test_modulated_signal_amplitude_bounds():
    t = sample_times(0.05, 10**5)
    x = modulated_signal(t, 60, 10**3)
    # Envelope (2 + sin) ranges in [1, 3], carrier in [-1, 1].
    assert np.max(np.abs(x)) <= 3.0 + 1e-9
