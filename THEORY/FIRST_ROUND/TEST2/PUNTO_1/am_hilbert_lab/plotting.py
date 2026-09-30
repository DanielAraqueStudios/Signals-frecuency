"""Matplotlib figure assembly for the AM/Hilbert/FIR-IIR exercises."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def plot_spectrum(freqs: np.ndarray, mag: np.ndarray, title: str, max_freq_hz: float | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(freqs, mag, color="tab:blue", linewidth=1.0)
    ax.set_xlabel("Frecuencia (Hz)")
    ax.set_ylabel("Magnitud")
    ax.set_title(title)
    if max_freq_hz is not None:
        ax.set_xlim(0, max_freq_hz)
    ax.grid(True, linestyle=":")
    fig.tight_layout()
    return fig


def plot_stacked_hilbert_filter(
    t: np.ndarray,
    original: np.ndarray,
    envelope: np.ndarray,
    filtered_envelope: np.ndarray,
    title: str,
    time_unit: str = "ms",
) -> plt.Figure:
    """Three stacked subplots: original signal, Hilbert magnitude, filtered Hilbert magnitude."""
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    fig.suptitle(title, fontsize=14, fontweight="bold")

    axes[0].plot(t, original, color="tab:gray", linewidth=0.7)
    axes[0].set_title("Señal original")
    axes[0].set_ylabel("Amplitud")
    axes[0].grid(True, linestyle=":")

    axes[1].plot(t, envelope, color="tab:orange", linewidth=1.0)
    axes[1].set_title("Magnitud de la transformada de Hilbert (envolvente)")
    axes[1].set_ylabel("Amplitud")
    axes[1].grid(True, linestyle=":")

    axes[2].plot(t, filtered_envelope, color="tab:purple", linewidth=1.2)
    axes[2].set_title("Envolvente filtrada")
    axes[2].set_xlabel(f"Tiempo ({time_unit})")
    axes[2].set_ylabel("Amplitud")
    axes[2].grid(True, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def plot_targeted_filter_attempt(
    t: np.ndarray,
    original: np.ndarray,
    fir_out: np.ndarray,
    iir_out: np.ndarray,
    freqs: np.ndarray,
    original_fft: np.ndarray,
    title: str,
    time_unit: str = "ms",
    max_freq_hz: float | None = None,
) -> plt.Figure:
    """Time-domain FIR/IIR outputs targeting the message frequency directly on the raw AM signal,
    plus the raw signal's spectrum to show there is no energy exactly at that frequency."""
    fig, axes = plt.subplots(2, 1, figsize=(11, 8))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    axes[0].plot(t, original, label="Original", color="tab:gray", linewidth=0.6, alpha=0.6)
    axes[0].plot(t, fir_out, label="FIR (orden 50)", color="tab:blue", linewidth=1.1)
    axes[0].plot(t, iir_out, label="IIR Butterworth", color="tab:red", linewidth=1.1, linestyle="--")
    axes[0].set_xlabel(f"Tiempo ({time_unit})")
    axes[0].set_ylabel("Amplitud")
    axes[0].set_title("Dominio del tiempo")
    axes[0].legend()
    axes[0].grid(True, linestyle=":")

    axes[1].plot(freqs, original_fft, color="tab:gray", linewidth=1.0)
    axes[1].set_xlabel("Frecuencia (Hz)")
    axes[1].set_ylabel("Magnitud")
    axes[1].set_title("Espectro de la señal AM original (sin energía aislada en f_mensaje)")
    if max_freq_hz is not None:
        axes[1].set_xlim(0, max_freq_hz)
    axes[1].grid(True, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig
