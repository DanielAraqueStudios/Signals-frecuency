import numpy as np

from am_lab.signals import sample_times, tone_signal
from am_lab.spectrum import single_sided_fft


def test_dominant_peak_matches_tone_frequency():
    fs = 10**5
    t = sample_times(0.05, fs)
    x = tone_signal(t, 60)
    freqs, magnitude = single_sided_fft(x, fs, max_freq_hz=200)
    peak_freq = freqs[np.argmax(magnitude)]
    assert abs(peak_freq - 60) < 5


def test_output_is_nonnegative_frequencies_only():
    fs = 10**5
    t = sample_times(0.01, fs)
    x = tone_signal(t, 60)
    freqs, _ = single_sided_fft(x, fs)
    assert np.all(freqs >= 0)


def test_max_freq_cap_is_respected():
    fs = 10**5
    t = sample_times(0.01, fs)
    x = tone_signal(t, 60)
    freqs, magnitude = single_sided_fft(x, fs, max_freq_hz=200)
    assert np.all(freqs <= 200)
    assert freqs.size == magnitude.size


def test_amplitude_normalization_recovers_unit_sine_amplitude():
    fs = 10**5
    t = sample_times(0.1, fs)
    x = tone_signal(t, 60)  # amplitude 1
    freqs, magnitude = single_sided_fft(x, fs, max_freq_hz=200)
    assert abs(np.max(magnitude) - 1.0) < 0.05
