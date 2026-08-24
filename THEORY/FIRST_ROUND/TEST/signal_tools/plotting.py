"""Plotting helpers for items 1-3. Each function returns an unshown Figure."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .csv_signal import dominant_frequency as csv_dominant_frequency
from .sampling import sine_wave
from .audio_fft import compute_fft_spectrum, dominant_frequency as audio_dominant_frequency


def plot_csv_signal(
    signal: np.ndarray, segments: list[np.ndarray], sample_rate: float
) -> plt.Figure:
    """Full signal in time, plus one FFT-spectrum subplot per segment."""
    t = np.arange(len(signal)) / sample_rate
    n_segs = len(segments)
    fig, axes = plt.subplots(n_segs + 1, 1, figsize=(10, 2.2 * (n_segs + 1)))

    axes[0].plot(t, signal, color="tab:blue")
    axes[0].set_title("Muestra01 - full signal in time", fontsize=10)
    axes[0].set_ylabel("Amplitude")
    axes[0].grid(True)

    for i, seg in enumerate(segments):
        freqs = np.fft.rfftfreq(len(seg), 1 / sample_rate)
        magnitude = np.abs(np.fft.rfft(seg)) / len(seg)
        peak = csv_dominant_frequency(seg, sample_rate)

        ax = axes[i + 1]
        ax.plot(freqs, magnitude, color="tab:orange")
        ax.set_title(f"Segment {i + 1} spectrum (dominant: {peak:.1f} Hz)", fontsize=9)
        ax.set_ylabel("Magnitude")
        ax.grid(True)

    axes[-1].set_xlabel("Frequency (Hz)")
    fig.subplots_adjust(hspace=0.45)
    return fig


def plot_sampling_quantization(
    frequency_hz: float,
    duration_s: float,
    sample_rates_hz: list[float],
    quantized_by_rate: dict[float, tuple[np.ndarray, np.ndarray]],
) -> plt.Figure:
    """Original analog sine (dotted) vs. sampled+quantized stems, one row per rate."""
    t_reference = np.linspace(0, duration_s, 10_000)
    reference = sine_wave(frequency_hz, t_reference)

    fig, axes = plt.subplots(len(sample_rates_hz), 1, figsize=(10, 2.6 * len(sample_rates_hz)), sharex=True)
    if len(sample_rates_hz) == 1:
        axes = [axes]

    for i, fs_m in enumerate(sample_rates_hz):
        t_samples, quantized = quantized_by_rate[fs_m]
        ax = axes[i]
        ax.plot(t_reference, reference, "k:", alpha=0.25, label="Original analog signal")
        ax.stem(
            t_samples,
            quantized,
            linefmt=f"C{i}-",
            markerfmt=f"C{i}o",
            basefmt="k-",
            label=f"Sampled and quantized (fs = {fs_m} Hz)",
        )
        ax.set_title(f"Sample rate: {fs_m} Hz", fontsize=10)
        ax.set_ylabel("Amplitude")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper right", fontsize=9)
        ax.set_ylim(-1.3, 1.3)

    axes[-1].set_xlabel("Time (s)")
    fig.subplots_adjust(hspace=0.3)
    return fig


def plot_audio_fft_comparison(spectra: dict[str, tuple[int, np.ndarray]]) -> plt.Figure:
    """Overlaid FFT magnitude spectra for each named audio signal."""
    fig, ax = plt.subplots(figsize=(12, 6))

    for name, (sample_rate, signal) in spectra.items():
        freqs, magnitude = compute_fft_spectrum(signal, sample_rate)
        peak = audio_dominant_frequency(freqs, magnitude)
        ax.plot(freqs, magnitude, label=f"{name} (fs={sample_rate} Hz, dom={peak:.0f} Hz)", alpha=0.7)

    ax.set_title("Frequency spectrum: violin, drum, cat")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Normalized magnitude")
    ax.set_xlim(0, 4000)
    ax.grid(True)
    ax.legend()
    return fig
