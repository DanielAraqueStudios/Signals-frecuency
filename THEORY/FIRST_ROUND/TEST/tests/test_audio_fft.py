import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signal_tools.audio_fft import compute_fft_spectrum, dominant_frequency

# load_wav is intentionally not unit-tested here: it reads real WAV files from
# disk via scipy.io.wavfile, which is thin I/O glue already exercised end to
# end by `python main.py` against the real audio_samples/*.wav recordings.


class TestComputeFftSpectrum:
    def test_pure_tone_dominant_bin(self):
        fs = 44100
        t = np.arange(fs) / fs
        signal = np.sin(2 * np.pi * 440 * t)
        freqs, magnitude = compute_fft_spectrum(signal, fs)
        peak_index = np.argmax(magnitude[1:]) + 1
        assert abs(freqs[peak_index] - 440) < 2

    def test_output_lengths_match(self):
        fs = 8000
        signal = np.random.default_rng(0).normal(size=500)
        freqs, magnitude = compute_fft_spectrum(signal, fs)
        assert len(freqs) == len(magnitude)


class TestDominantFrequency:
    def test_ignores_dc_component(self):
        freqs = np.array([0.0, 100.0, 200.0])
        magnitude = np.array([10.0, 1.0, 0.5])  # DC dominates, should be skipped
        assert dominant_frequency(freqs, magnitude) == 100.0

    def test_single_bin_returns_zero(self):
        assert dominant_frequency(np.array([0.0]), np.array([1.0])) == 0.0
