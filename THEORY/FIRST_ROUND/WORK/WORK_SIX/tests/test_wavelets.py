import numpy as np
import pytest

pywt = pytest.importorskip("pywt")

from wavelet_lab.wavelets import cwt_scalogram


def test_cwt_scalogram_shape():
    sample_rate = 1000
    t = np.arange(sample_rate) / sample_rate
    signal = np.sin(2 * np.pi * 50 * t)

    energy, frequencies, times = cwt_scalogram(signal, sample_rate, n_scales=16)

    assert energy.shape == (16, signal.size)
    assert frequencies.shape == (16,)
    assert times.shape == (signal.size,)


def test_cwt_scalogram_frequencies_within_requested_range():
    sample_rate = 1000
    signal = np.sin(2 * np.pi * 50 * np.arange(sample_rate) / sample_rate)

    _, frequencies, _ = cwt_scalogram(signal, sample_rate, n_scales=8, fmin=20.0, fmax=200.0)

    assert frequencies.min() >= 15.0  # small tolerance from pywt's discretization
    assert frequencies.max() <= 210.0


def test_cwt_scalogram_energy_is_nonnegative():
    sample_rate = 500
    signal = np.random.default_rng(0).normal(size=500)

    energy, _, _ = cwt_scalogram(signal, sample_rate, n_scales=8)

    assert np.all(energy >= 0)


def test_cwt_scalogram_rejects_empty_signal():
    with pytest.raises(ValueError):
        cwt_scalogram(np.array([]), sample_rate=1000)


def test_cwt_scalogram_detects_dominant_frequency():
    # A pure 50 Hz tone should have its energy concentrated near 50 Hz.
    sample_rate = 1000
    t = np.arange(sample_rate) / sample_rate
    signal = np.sin(2 * np.pi * 50 * t)

    energy, frequencies, _ = cwt_scalogram(signal, sample_rate, n_scales=32, fmin=10.0, fmax=200.0)

    mean_energy_per_freq = energy.mean(axis=1)
    peak_freq = frequencies[np.argmax(mean_energy_per_freq)]
    assert 35.0 <= peak_freq <= 65.0
