import numpy as np
import pytest

from modulation_lab.modulation import am_modulate, lowpass_fft


def _tone(freq_hz: float, sample_rate: float, duration_s: float = 0.05) -> np.ndarray:
    t = np.arange(int(sample_rate * duration_s)) / sample_rate
    return np.sin(2 * np.pi * freq_hz * t)


def test_am_modulate_rejects_empty_message():
    with pytest.raises(ValueError):
        am_modulate(np.array([]), sample_rate=50_000)


def test_am_modulate_output_length_matches_input():
    message = _tone(440, 50_000)
    out = am_modulate(message, sample_rate=50_000, carrier_freq_hz=10_000)
    assert out.size == message.size


@pytest.mark.parametrize("target_fs", [50_000, 500_000])
def test_am_modulate_spectrum_has_carrier_and_sidebands(target_fs):
    # Synthetic tone standing in for the cat audio (avoids depending on the
    # real recording / librosa for a deterministic unit test).
    message_freq = 500.0
    carrier_freq = 10_000.0
    message = _tone(message_freq, target_fs, duration_s=0.05)

    modulated = am_modulate(message, sample_rate=target_fs, carrier_freq_hz=carrier_freq)

    n = modulated.size
    freqs = np.fft.fftfreq(n, d=1.0 / target_fs)
    magnitude = np.abs(np.fft.fft(modulated)) / (n / 2)

    def peak_near(target_freq: float, tol_hz: float = 50.0) -> float:
        mask = np.abs(freqs - target_freq) <= tol_hz
        return magnitude[mask].max()

    carrier_peak = peak_near(carrier_freq)
    lower_sideband_peak = peak_near(carrier_freq - message_freq)
    upper_sideband_peak = peak_near(carrier_freq + message_freq)
    off_band_floor = peak_near(carrier_freq + 3 * message_freq)

    assert carrier_peak > 0.5
    assert lower_sideband_peak > 0.1
    assert upper_sideband_peak > 0.1
    assert off_band_floor < 0.05


def test_lowpass_fft_removes_high_frequency_content():
    sample_rate = 50_000
    low = _tone(200, sample_rate)
    high = _tone(20_000, sample_rate)
    mixed = low + high

    filtered = lowpass_fft(mixed, sample_rate, cutoff_hz=8_000)

    freqs = np.fft.fftfreq(filtered.size, d=1.0 / sample_rate)
    magnitude = np.abs(np.fft.fft(filtered)) / (filtered.size / 2)

    low_peak = magnitude[np.abs(freqs - 200) <= 20].max()
    high_peak = magnitude[np.abs(freqs - 20_000) <= 20].max()

    assert low_peak > 0.5
    assert high_peak < 0.05


def test_lowpass_fft_preserves_length():
    signal = np.random.default_rng(0).normal(size=1000)
    out = lowpass_fft(signal, sample_rate=50_000, cutoff_hz=8_000)
    assert out.size == signal.size
