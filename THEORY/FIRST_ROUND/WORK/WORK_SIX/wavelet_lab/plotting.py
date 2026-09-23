"""Matplotlib figure assembly for WORK_SIX: wavelet scalograms and the
100-element correlation output vector.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def plot_scalogram(energy: np.ndarray, frequencies: np.ndarray, times: np.ndarray, title: str) -> plt.Figure:
    """Plot a CWT energy scalogram (time on x, frequency on y, energy as color).

    Args:
        energy: `(n_scales, n_samples)` array from `cwt_scalogram`.
        frequencies: `(n_scales,)` array of Hz.
        times: `(n_samples,)` array of seconds.
        title: Figure title.

    Returns:
        The assembled figure (not shown or saved).
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    mesh = ax.pcolormesh(times, frequencies, energy, shading="gouraud", cmap="viridis")
    ax.set_yscale("log")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Frecuencia (Hz)")
    ax.set_title(title, fontsize=12, fontweight="bold")
    fig.colorbar(mesh, ax=ax, label="Energía |CWT|²")
    fig.tight_layout()
    return fig


def plot_correlation_vector(output_vector: np.ndarray, block_boundaries: list[int], vector_names: list[str]) -> plt.Figure:
    """Plot the 100-element correlation output vector, marking each vector's block.

    Args:
        output_vector: Length-100 array from `correlation_vector_100`.
        block_boundaries: Cumulative end-index of each vector's block
            (e.g. `[17, 34, 51, 68, 84, 100]`).
        vector_names: Names matching `block_boundaries` (e.g. `["Vector1", ...]`).

    Returns:
        The assembled figure (not shown or saved).
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(np.arange(output_vector.size), output_vector, "b-o", markersize=3, linewidth=1)

    start = 0
    for end, name in zip(block_boundaries, vector_names):
        ax.axvspan(start, end, alpha=0.1)
        ax.text((start + end) / 2, ax.get_ylim()[1], name, ha="center", va="bottom", fontsize=8)
        start = end

    ax.set_xlabel("Posición en el vector de salida (0-99)")
    ax.set_ylabel("Correlación (suma de productos)")
    ax.set_title("Vector de salida de 100 posiciones (Tarea 2, Parte 1)", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)
    fig.tight_layout()
    return fig
