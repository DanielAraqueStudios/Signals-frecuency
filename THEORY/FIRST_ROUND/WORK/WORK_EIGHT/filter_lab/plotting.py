"""Matplotlib figure assembly: before/after spectra (item A) and
manual-vs-scipy comparison (item B).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def _single_sided_fft(x: np.ndarray, fs: float) -> tuple[np.ndarray, np.ndarray]:
    n = x.size
    freqs = np.fft.fftfreq(n, 1 / fs)
    pos = freqs >= 0
    mag = np.abs(np.fft.fft(x))[pos] / (n / 2)
    return freqs[pos], mag


def plot_before_after_spectrum(t: np.ndarray, x: np.ndarray, y: np.ndarray, fs: float, title: str) -> plt.Figure:
    """Time-domain + spectrum, input vs. filtered output, stacked."""
    freqs_x, mag_x = _single_sided_fft(x, fs)
    freqs_y, mag_y = _single_sided_fft(y, fs)
    f_max = min(fs / 2, 600.0)

    fig, axes = plt.subplots(2, 2, figsize=(12, 7))
    fig.suptitle(title, fontsize=13, fontweight="bold")

    axes[0, 0].plot(t * 1000, x, "b-", linewidth=0.8)
    axes[0, 0].set_title("Entrada x[n]")
    axes[0, 0].set_xlabel("Tiempo (ms)")
    axes[0, 0].grid(True, linestyle=":")

    axes[0, 1].plot(t * 1000, y, "r-", linewidth=0.8)
    axes[0, 1].set_title("Salida filtrada y[n]")
    axes[0, 1].set_xlabel("Tiempo (ms)")
    axes[0, 1].grid(True, linestyle=":")

    mask_x = freqs_x <= f_max
    axes[1, 0].stem(freqs_x[mask_x], mag_x[mask_x], linefmt="b-", markerfmt="bo", basefmt="k-")
    axes[1, 0].set_title("Espectro de entrada")
    axes[1, 0].set_xlabel("Frecuencia (Hz)")
    axes[1, 0].grid(True, linestyle=":")

    mask_y = freqs_y <= f_max
    axes[1, 1].stem(freqs_y[mask_y], mag_y[mask_y], linefmt="r-", markerfmt="ro", basefmt="k-")
    axes[1, 1].set_title("Espectro filtrado")
    axes[1, 1].set_xlabel("Frecuencia (Hz)")
    axes[1, 1].grid(True, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


def plot_manual_vs_scipy(t: np.ndarray, y_manual: np.ndarray, y_scipy: np.ndarray, title: str) -> plt.Figure:
    """Overlaid time-domain output + absolute difference, manual vs. scipy."""
    diff = y_manual - y_scipy

    fig, (ax_overlay, ax_diff) = plt.subplots(2, 1, figsize=(10, 7))
    fig.suptitle(title, fontsize=13, fontweight="bold")

    ax_overlay.plot(t * 1000, y_manual, "r-", linewidth=1.2, label="Manual (ciclo for)")
    ax_overlay.plot(t * 1000, y_scipy, "b--", linewidth=1.0, label="scipy.signal.lfilter")
    ax_overlay.set_ylabel("Amplitud")
    ax_overlay.set_title("Salidas superpuestas")
    ax_overlay.legend()
    ax_overlay.grid(True, linestyle=":")

    ax_diff.plot(t * 1000, diff, "k-", linewidth=0.8)
    ax_diff.set_xlabel("Tiempo (ms)")
    ax_diff.set_ylabel("y_manual - y_scipy")
    ax_diff.set_title(f"Diferencia (max|diff| = {np.max(np.abs(diff)):.3e})")
    ax_diff.grid(True, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig
