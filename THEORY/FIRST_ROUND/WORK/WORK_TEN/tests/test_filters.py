import numpy as np

from fir_iir_lab.filters import apply_filter, design_fir_lowpass, design_iir_lowpass
from fir_iir_lab.signals import sample_times, tone_signal
from fir_iir_lab.spectrum import single_sided_fft


def _passband_and_stopband_tones(fs, cutoff):
    t = sample_times(0.2, fs)
    passband = tone_signal(t, cutoff * 0.1)
    stopband = tone_signal(t, cutoff * 5)
    return t, passband + stopband


def test_fir_lowpass_attenuates_stopband_relative_to_passband():
    fs = 10_000
    cutoff = 300
    t, x = _passband_and_stopband_tones(fs, cutoff)
    b = design_fir_lowpass(cutoff, fs, order=100)
    y = apply_filter(b, [1.0], x)

    freqs, mag_in = single_sided_fft(x, fs, max_freq_hz=fs / 2)
    _, mag_out = single_sided_fft(y, fs, max_freq_hz=fs / 2)

    stop_idx = np.argmin(np.abs(freqs - cutoff * 5))
    assert mag_out[stop_idx] < 0.1 * mag_in[stop_idx]


def test_iir_lowpass_attenuates_stopband_relative_to_passband():
    fs = 10_000
    cutoff = 300
    t, x = _passband_and_stopband_tones(fs, cutoff)
    b, a = design_iir_lowpass(cutoff, fs, order=4)
    y = apply_filter(b, a, x)

    freqs, mag_in = single_sided_fft(x, fs, max_freq_hz=fs / 2)
    _, mag_out = single_sided_fft(y, fs, max_freq_hz=fs / 2)

    stop_idx = np.argmin(np.abs(freqs - cutoff * 5))
    assert mag_out[stop_idx] < 0.1 * mag_in[stop_idx]


def test_fir_lowpass_passes_passband_tone():
    fs = 10_000
    cutoff = 300
    t = sample_times(0.2, fs)
    x = tone_signal(t, cutoff * 0.1)
    b = design_fir_lowpass(cutoff, fs, order=100)
    y = apply_filter(b, [1.0], x)
    steady = slice(len(y) // 4, -len(y) // 4)
    assert np.std(y[steady]) > 0.5 * np.std(x[steady])
