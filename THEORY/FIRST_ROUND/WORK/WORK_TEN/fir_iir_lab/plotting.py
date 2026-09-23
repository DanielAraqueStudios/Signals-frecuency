"""Matplotlib figure assembly for the FIR/IIR/Hilbert exercises."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def plot_filter_comparison(
    t: np.ndarray,
    original: np.ndarray,
    fir_out: np.ndarray,
    iir_out: np.ndarray,
    freqs: np.ndarray,
    original_fft: np.ndarray,
    fir_fft: np.ndarray,
    iir_fft: np.ndarray,
    title: str,
    time_unit: str = "s",
) -> plt.Figure:
    """Time + frequency domain comparison of original vs. FIR- vs. IIR-filtered."""
    fig, axes = plt.subplots(2, 1, figsize=(11, 8))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    axes[0].plot(t, original, label="Original", color="tab:gray", linewidth=0.8, alpha=0.7)
    axes[0].plot(t, fir_out, label="FIR", color="tab:blue", linewidth=1.0)
    axes[0].plot(t, iir_out, label="IIR", color="tab:red", linewidth=1.0, linestyle="--")
    axes[0].set_xlabel(f"Tiempo ({time_unit})")
    axes[0].set_ylabel("Amplitud")
    axes[0].set_title("Dominio del tiempo")
    axes[0].legend()
    axes[0].grid(True, linestyle=":")

    axes[1].plot(freqs, original_fft, label="Original", color="tab:gray", linewidth=0.8, alpha=0.7)
    axes[1].plot(freqs, fir_fft, label="FIR", color="tab:blue", linewidth=1.2)
    axes[1].plot(freqs, iir_fft, label="IIR", color="tab:red", linewidth=1.2, linestyle="--")
    axes[1].set_xlabel("Frecuencia (Hz)")
    axes[1].set_ylabel("Magnitud")
    axes[1].set_title("Dominio de la frecuencia")
    axes[1].legend()
    axes[1].grid(True, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def plot_negative_freq_removal(
    t: np.ndarray, original: np.ndarray, analytic: np.ndarray, title: str, time_unit: str = "ms"
) -> plt.Figure:
    """Original real signal vs. real/imag parts of its negative-freq-removed version."""
    fig, axes = plt.subplots(2, 1, figsize=(11, 7))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    axes[0].plot(t, original, color="tab:orange", linewidth=1.0)
    axes[0].set_title("Señal original")
    axes[0].set_ylabel("Amplitud")
    axes[0].grid(True, linestyle=":")

    axes[1].plot(t, analytic.real, label="Re", color="tab:blue", linewidth=1.0)
    axes[1].plot(t, analytic.imag, label="Im", color="tab:green", linewidth=1.0)
    axes[1].plot(t, np.abs(analytic), label="|.|  (envolvente)", color="tab:red", linewidth=1.2)
    axes[1].set_title("Tras eliminar frecuencias negativas (FFT)")
    axes[1].set_xlabel(f"Tiempo ({time_unit})")
    axes[1].set_ylabel("Amplitud")
    axes[1].legend()
    axes[1].grid(True, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


def plot_hilbert_envelope_filtered(
    t: np.ndarray, envelope: np.ndarray, filtered_envelope: np.ndarray, title: str, time_unit: str = "s"
) -> plt.Figure:
    """Hilbert envelope before/after the 300 Hz filter."""
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(t, envelope, label="Envolvente Hilbert", color="tab:gray", linewidth=0.9, alpha=0.7)
    ax.plot(t, filtered_envelope, label="Envolvente filtrada (300 Hz)", color="tab:purple", linewidth=1.2)
    ax.set_title(title)
    ax.set_xlabel(f"Tiempo ({time_unit})")
    ax.set_ylabel("Amplitud")
    ax.legend()
    ax.grid(True, linestyle=":")
    fig.tight_layout()
    return fig


def plot_order_sweep(
    t: np.ndarray,
    original: np.ndarray,
    outputs_by_order: dict[int, np.ndarray],
    freqs: np.ndarray,
    ffts_by_order: dict[int, np.ndarray],
    title: str,
    time_unit: str = "ms",
) -> plt.Figure:
    """Time + frequency domain comparison across increasing filter orders (task 6.4)."""
    fig, axes = plt.subplots(2, 1, figsize=(11, 8))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    axes[0].plot(t, original, label="Original", color="black", linewidth=0.7, alpha=0.4)
    for order, y in outputs_by_order.items():
        axes[0].plot(t, y, label=f"orden {order}", linewidth=1.0)
    axes[0].set_xlabel(f"Tiempo ({time_unit})")
    axes[0].set_ylabel("Amplitud")
    axes[0].set_title("Dominio del tiempo")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, linestyle=":")

    for order, mag in ffts_by_order.items():
        axes[1].plot(freqs, mag, label=f"orden {order}", linewidth=1.2)
    axes[1].set_xlabel("Frecuencia (Hz)")
    axes[1].set_ylabel("Magnitud")
    axes[1].set_title("Dominio de la frecuencia")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig
