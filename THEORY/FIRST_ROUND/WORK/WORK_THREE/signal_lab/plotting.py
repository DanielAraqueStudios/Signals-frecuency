"""Matplotlib figure assembly for every sampling/synthesis exercise.

Each function here only arranges already-computed signals (from
`waveforms.py` and `spectral.py`) into a figure — no synthesis math lives
in this module, mirroring the split used in `WORK_TWO/fourier_square`.
"""

from __future__ import annotations

from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np

from .spectral import compute_fft
from .waveforms import (
    sample_times,
    sine_wave,
    square_wave_fourier,
    square_wave_ideal,
    triangular_wave,
)

# Dense reference rate used to draw a "continuous-looking" backing curve
# behind the discrete samples in every sampling-comparison plot.
REFERENCE_RATE_HZ = 200_000


def plot_sine_sampling_grid(
    frequency_hz: float, duration_s: float, sample_rates: Sequence[float]
) -> plt.Figure:
    """Item 4: sample a pure sine wave at several sampling rates.

    One subplot per entry in `sample_rates`: a dense reference sine
    overlaid with its discrete samples, making it easy to see aliasing
    when `sample_rate < 2 * frequency_hz` (the Nyquist limit).

    Args:
        frequency_hz: Sine frequency (Hz).
        duration_s: Length of the time window in seconds.
        sample_rates: Sampling rates (Hz) to compare, one subplot each.

    Returns:
        The assembled figure (not shown or saved).
    """
    t_ref = sample_times(duration_s, REFERENCE_RATE_HZ)
    ref = sine_wave(t_ref, frequency_hz)

    fig, axes = plt.subplots(len(sample_rates), 1, figsize=(10, 10), sharex=True)
    fig.suptitle(
        f"Muestreo de seno de {frequency_hz / 1000:.0f} kHz "
        f"(Nyquist = {2 * frequency_hz / 1000:.0f} kHz)",
        fontsize=14,
        fontweight="bold",
    )

    for ax, rate in zip(np.atleast_1d(axes), sample_rates):
        t = sample_times(duration_s, rate)
        samples = sine_wave(t, frequency_hz)
        aliased = " (ALIASING)" if rate < 2 * frequency_hz else ""
        ax.plot(t_ref, ref, "b--", alpha=0.4, label="Referencia continua")
        ax.plot(t, samples, "ro-", markersize=3, alpha=0.8, label=f"fs={rate / 1000:g} kHz{aliased}")
        ax.set_ylabel(f"{rate / 1000:g} kHz")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper right", fontsize=8)

    np.atleast_1d(axes)[-1].set_xlabel("Tiempo (s)")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def plot_square_construction(w0: float, duration_s: float, harmonics_list: Sequence[int]) -> plt.Figure:
    """Item 5: build a square wave from an increasing number of harmonics.

    One subplot per entry in `harmonics_list`, each drawn at a dense
    reference rate so the reconstructed waveform reads as continuous —
    this exercise is about harmonic count, not sampling.

    Args:
        w0: Fundamental angular frequency (rad/s).
        duration_s: Length of the time window in seconds.
        harmonics_list: Number of harmonics to reconstruct, one subplot
            per value.

    Returns:
        The assembled figure (not shown or saved).
    """
    t = sample_times(duration_s, REFERENCE_RATE_HZ)

    fig, axes = plt.subplots(len(harmonics_list), 1, figsize=(10, 10), sharex=True)
    fig.suptitle("Construcción de onda cuadrada por serie de Fourier", fontsize=14, fontweight="bold")

    for ax, num_harmonics in zip(np.atleast_1d(axes), harmonics_list):
        f_t = square_wave_fourier(t, w0, num_harmonics)
        ax.plot(t, f_t, "b-", linewidth=1.2)
        ax.set_ylabel(f"N={num_harmonics}")
        ax.grid(True, linestyle=":", alpha=0.6)

    np.atleast_1d(axes)[-1].set_xlabel("Tiempo (s)")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def plot_triangular_sampling_grid(
    frequency_hz: float, duration_s: float, v_max: float, v_min: float, sample_rates: Sequence[float]
) -> plt.Figure:
    """Item 6: sample an offset triangular wave at several sampling rates.

    Args:
        frequency_hz: Triangular-wave frequency (Hz).
        duration_s: Length of the time window in seconds.
        v_max: Peak voltage.
        v_min: Trough voltage.
        sample_rates: Sampling rates (Hz) to compare, one subplot each.

    Returns:
        The assembled figure (not shown or saved).
    """
    t_ref = sample_times(duration_s, REFERENCE_RATE_HZ)
    ref = triangular_wave(t_ref, frequency_hz, v_max, v_min)

    fig, axes = plt.subplots(len(sample_rates), 1, figsize=(10, 10), sharex=True)
    fig.suptitle(
        f"Muestreo de triangular {frequency_hz / 1000:.0f} kHz "
        f"(Vmax={v_max}, Vmin={v_min})",
        fontsize=14,
        fontweight="bold",
    )

    for ax, rate in zip(np.atleast_1d(axes), sample_rates):
        t = sample_times(duration_s, rate)
        samples = triangular_wave(t, frequency_hz, v_max, v_min)
        ax.plot(t_ref, ref, "b--", alpha=0.4, label="Referencia continua")
        ax.plot(t, samples, "go-", markersize=3, alpha=0.8, label=f"fs={rate / 1000:g} kHz")
        ax.set_ylabel(f"{rate / 1000:g} kHz")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper right", fontsize=8)

    np.atleast_1d(axes)[-1].set_xlabel("Tiempo (s)")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def plot_square_sampling_grid(
    w0: float, duration_s: float, harmonics_list: Sequence[int], sample_rate: float
) -> plt.Figure:
    """Item 7: sample a Fourier-series square wave at one sampling rate.

    One subplot per entry in `harmonics_list`: the reconstructed signal
    overlaid with its samples at `sample_rate`.

    Args:
        w0: Fundamental angular frequency (rad/s).
        duration_s: Length of the time window in seconds.
        harmonics_list: Number of harmonics to reconstruct, one subplot
            per value.
        sample_rate: Sampling rate (Hz) used to mark individual samples.

    Returns:
        The assembled figure (not shown or saved).
    """
    t_ref = sample_times(duration_s, REFERENCE_RATE_HZ)
    t = sample_times(duration_s, sample_rate)

    fig, axes = plt.subplots(len(harmonics_list), 1, figsize=(10, 10), sharex=True)
    fig.suptitle(
        f"Muestreo de onda cuadrada: fs = {sample_rate / 1000:g} kHz",
        fontsize=14,
        fontweight="bold",
    )

    for ax, num_harmonics in zip(np.atleast_1d(axes), harmonics_list):
        f_ref = square_wave_fourier(t_ref, w0, num_harmonics)
        f_t = square_wave_fourier(t, w0, num_harmonics)
        ax.plot(t_ref, f_ref, "b--", alpha=0.5, label="Señal reconstruida")
        ax.plot(t, f_t, "ro", markersize=2, alpha=0.6, label=f"Muestras (fs={sample_rate / 1000:g}kHz)")
        ax.set_ylabel(f"N={num_harmonics}")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper right", fontsize=8)

    np.atleast_1d(axes)[-1].set_xlabel("Tiempo (s)")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def plot_fft_comparison(
    frequency_hz: float, duration_s: float, sample_rate: float, num_harmonics: int
) -> plt.Figure:
    """Item 9: compare the FFT of an ideal square wave vs. its N-harmonic reconstruction.

    Top row: time-domain overlay of both signals. Bottom row: their
    single-sided FFT magnitude spectra side by side, so the missing
    higher-order odd harmonics in the truncated reconstruction are
    directly visible as absent spectral lines.

    Args:
        frequency_hz: Square-wave fundamental frequency (Hz).
        duration_s: Length of the time window in seconds.
        sample_rate: Sampling rate (Hz) used for both signals.
        num_harmonics: Number of harmonics used in the reconstruction
            (e.g. 10, matching item 5/7's construction exercise).

    Returns:
        The assembled figure (not shown or saved).
    """
    w0 = 2 * np.pi * frequency_hz
    t = sample_times(duration_s, sample_rate)

    ideal = square_wave_ideal(t, frequency_hz)
    reconstructed = square_wave_fourier(t, w0, num_harmonics)

    freqs_ideal, mag_ideal = compute_fft(ideal, sample_rate)
    freqs_recon, mag_recon = compute_fft(reconstructed, sample_rate)

    freq_limit = frequency_hz * (2 * num_harmonics + 5)

    fig, (ax_time, ax_freq) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle("Ideal vs. reconstrucción por serie de Fourier (N armónicos)", fontsize=14, fontweight="bold")

    ax_time.plot(t, ideal, "k-", linewidth=1, alpha=0.6, label="Cuadrada ideal")
    ax_time.plot(t, reconstructed, "r--", linewidth=1.2, label=f"Reconstrucción N={num_harmonics}")
    ax_time.set_xlabel("Tiempo (s)")
    ax_time.set_ylabel("Amplitud")
    ax_time.grid(True, linestyle=":", alpha=0.6)
    ax_time.legend(loc="upper right", fontsize=8)

    mask_ideal = freqs_ideal <= freq_limit
    mask_recon = freqs_recon <= freq_limit
    ax_freq.stem(freqs_ideal[mask_ideal], mag_ideal[mask_ideal], linefmt="k-", markerfmt="ko", basefmt=" ", label="FFT ideal")
    ax_freq.stem(freqs_recon[mask_recon], mag_recon[mask_recon], linefmt="r-", markerfmt="rx", basefmt=" ", label=f"FFT N={num_harmonics}")
    ax_freq.set_xlabel("Frecuencia (Hz)")
    ax_freq.set_ylabel("Magnitud")
    ax_freq.grid(True, linestyle=":", alpha=0.6)
    ax_freq.legend(loc="upper right", fontsize=8)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig
