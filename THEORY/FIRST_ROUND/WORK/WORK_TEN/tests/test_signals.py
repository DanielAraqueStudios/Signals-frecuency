import numpy as np

from fir_iir_lab.signals import am_modulate, sample_times, tone_signal


def test_am_modulate_matches_closed_form():
    t = sample_times(0.01, 1000)
    message = 2 + tone_signal(t, 60)
    expected = message * np.sin(2 * np.pi * 100 * t)
    np.testing.assert_allclose(am_modulate(message, t, 100), expected)


def test_tone_signal_matches_closed_form():
    t = sample_times(0.01, 1000)
    expected = np.sin(2 * np.pi * 60 * t)
    np.testing.assert_allclose(tone_signal(t, 60), expected)
