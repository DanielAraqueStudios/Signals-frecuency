import numpy as np

from avg_filter_lab.waveforms import sample_times, sine_am, sine_tone, square_am, square_tone


def test_sample_times_covers_expected_window():
    t = sample_times(0.01, 1000)
    assert t[0] == 0
    assert t[-1] < 0.01
    assert t.size == 10


def test_sine_tone_matches_closed_form():
    t = sample_times(0.01, 10_000)
    expected = np.sin(2 * np.pi * 100 * t)
    np.testing.assert_allclose(sine_tone(t, 100), expected)


def test_sine_am_matches_closed_form():
    t = sample_times(0.01, 10_000)
    expected = (2 + np.sin(2 * np.pi * 60 * t)) * np.sin(2 * np.pi * 1000 * t)
    np.testing.assert_allclose(sine_am(t, 60, 1000), expected)


def test_square_tone_is_bounded_and_bipolar():
    t = sample_times(0.05, 10_000)
    x = square_tone(t, 60)
    assert np.all(np.isin(x, [-1.0, 1.0]))


def test_square_am_matches_closed_form():
    t = sample_times(0.01, 10_000)
    from scipy import signal as scipy_signal

    expected = (2 + scipy_signal.square(2 * np.pi * 60 * t)) * scipy_signal.square(
        2 * np.pi * 1000 * t
    )
    np.testing.assert_allclose(square_am(t, 60, 1000), expected)
