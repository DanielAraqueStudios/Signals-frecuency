"""Matplotlib figure assembly for the convolution exercises.

One figure per kernel: input segment, kernel (stem plot — it's a short
discrete vector, not a dense waveform), and the resulting convolved
segment, all sharing a sample-index x-axis so the kernel's relative
length/shape is visible against the signal it's applied to.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def plot_convolution(x: np.ndarray, h: np.ndarray, y: np.ndarray, title: str) -> plt.Figure:
    """Plot input segment, kernel, and convolution output stacked vertically.

    Args:
        x: Input signal segment (time domain, already windowed short).
        h: Kernel / impulse response.
        y: `convolve(x, h)` (or `manual_convolve(x, h)`) result.
        title: Figure title (also identifies the kernel, e.g. "step_10").

    Returns:
        The assembled figure (not shown or saved).
    """
    fig, (ax_x, ax_h, ax_y) = plt.subplots(3, 1, figsize=(10, 8))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    ax_x.plot(np.arange(x.size), x, "b-", linewidth=0.8)
    ax_x.set_ylabel("x[n]")
    ax_x.set_title("Segmento de entrada (audio 'gato')", fontsize=10)
    ax_x.grid(True, linestyle=":", alpha=0.6)

    ax_h.stem(np.arange(h.size), h, linefmt="g-", markerfmt="go", basefmt=" ")
    ax_h.set_ylabel("h[n]")
    ax_h.set_ylim(-0.2, 1.2)
    ax_h.set_title(f"Kernel (largo={h.size})", fontsize=10)
    ax_h.grid(True, linestyle=":", alpha=0.6)

    ax_y.plot(np.arange(y.size), y, "r-", linewidth=0.8)
    ax_y.set_ylabel("y[n] = x[n] * h[n]")
    ax_y.set_xlabel("n (muestra)")
    ax_y.set_title("Salida de la convolución", fontsize=10)
    ax_y.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig
