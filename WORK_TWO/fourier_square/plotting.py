"""Matplotlib visualizations for the Fourier square-wave reconstruction."""

from __future__ import annotations

from typing import Sequence

import matplotlib.pyplot as plt

from .synthesis import fourier_square_wave, sample_times


def plot_sampling_rate_grid(
    w0: float,
    duration_s: float,
    harmonics_list: Sequence[int],
    sample_rate: int,
) -> plt.Figure:
    """Build a stacked-subplot figure comparing reconstructions at one sample rate.

    One subplot per entry in `harmonics_list`: the reconstructed signal
    (dashed line) overlaid with its samples at `sample_rate` (red dots).
    Together the subplots show how the Gibbs overshoot near discontinuities
    persists regardless of harmonic count, while stepping `sample_rate`
    across figures shows how sample density changes independently of it.

    Args:
        w0: Fundamental angular frequency (rad/s).
        duration_s: Length of the time window in seconds.
        harmonics_list: Number of harmonics to reconstruct, one subplot
            per value.
        sample_rate: Sampling rate (Hz) used both to build the time axis
            and to mark individual samples.

    Returns:
        The assembled Matplotlib figure (not shown or saved).
    """
    t = sample_times(duration_s, sample_rate)
    sample_period_ms = 1000 / sample_rate

    fig, axes = plt.subplots(len(harmonics_list), 1, figsize=(10, 10), sharex=True)
    fig.suptitle(
        f"Frecuencia de Muestreo: {sample_rate / 1000:.2f} kHz "
        f"(Ts = {sample_period_ms:.4f} ms)",
        fontsize=14,
        fontweight="bold",
    )

    for ax, num_harmonics in zip(axes, harmonics_list):
        f_t = fourier_square_wave(t, w0, num_harmonics)
        ax.plot(t, f_t, "b--", alpha=0.7, label="Señal reconstruida")
        ax.plot(t, f_t, "ro", markersize=2, alpha=0.5, label=f"Muestras (fs={sample_rate}Hz)")
        ax.set_ylabel(f"N={num_harmonics}")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper right", fontsize=8)

    axes[-1].set_xlabel("Tiempo (s)")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig
