import numpy as np

from lms_lab.signals import sample_times, tone_signal, white_noise


def test_tone_signal_matches_closed_form():
    t = sample_times(0.01, 1000)
    expected = 2.0 * np.sin(2 * np.pi * 60 * t)
    np.testing.assert_allclose(tone_signal(t, 60, amplitude=2.0), expected)


def test_white_noise_matches_requested_power():
    rng = np.random.default_rng(0)
    noise = white_noise(200_000, power=4.0, rng=rng)
    assert np.isclose(np.var(noise), 4.0, rtol=0.05)
    assert np.isclose(np.mean(noise), 0.0, atol=0.05)
