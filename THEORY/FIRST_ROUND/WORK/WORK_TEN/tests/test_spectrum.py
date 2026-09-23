import numpy as np

from fir_iir_lab.signals import sample_times, tone_signal
from fir_iir_lab.spectrum import remove_negative_frequencies, single_sided_fft


def test_remove_negative_frequencies_zeroes_negative_bins():
    t = sample_times(0.1, 10_000)
    x = tone_signal(t, 100)
    analytic = remove_negative_frequencies(x)
    spectrum = np.fft.fft(analytic)
    freqs = np.fft.fftfreq(x.size)
    assert np.allclose(spectrum[freqs < 0], 0.0)


def test_remove_negative_frequencies_reconstructs_positive_tone():
    fs = 10_000
    t = sample_times(0.1, fs)
    x = tone_signal(t, 100)
    analytic = remove_negative_frequencies(x)
    # Half-analytic signal of a real sine has a constant envelope (0.5,
    # since negative bins are zeroed rather than doubling the positive half).
    steady = np.abs(analytic)[50:-50]
    assert np.allclose(steady, 0.5, atol=0.05)


def test_single_sided_fft_peak_matches_tone_frequency():
    fs = 10_000
    t = sample_times(0.5, fs)
    x = tone_signal(t, 250)
    freqs, mag = single_sided_fft(x, fs, max_freq_hz=1000)
    peak_freq = freqs[np.argmax(mag)]
    assert abs(peak_freq - 250) < 5
