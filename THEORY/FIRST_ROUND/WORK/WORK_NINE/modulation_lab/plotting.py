"""Matplotlib figure assembly for the modulation exercise.

Two panels per figure: a short time-domain segment (the modulated envelope
is only visible over a few carrier cycles, not the whole recording) and the
single-sided FFT (showing the carrier + AM sidebands).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def plot_modulation(signal: np.ndarray, sample_rate: float, title: str, segment_s: float = 0.01) -> plt.Figure:
    """Plot a time-domain segment and the FFT of a modulated signal.

    Args:
        signal: Modulated signal (full length).
        sample_rate: Samples per second (Hz).
        title: Figure title (identifies the target sample rate).
        segment_s: Duration of the time-domain segment to plot, in seconds.

    Returns:
        The assembled figure (not shown or saved).
    """
    fig, (ax_t, ax_f) = plt.subplots(2, 1, figsize=(10, 7))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    n_seg = max(1, int(segment_s * sample_rate))
    seg = signal[:n_seg]
    t_ms = np.arange(seg.size) / sample_rate * 1000
    ax_t.plot(t_ms, seg, "b-", linewidth=0.8)
    ax_t.set_xlabel("Tiempo (ms)")
    ax_t.set_ylabel("Amplitud")
    ax_t.set_title(f"Señal modulada (primeros {segment_s * 1000:.0f} ms)", fontsize=10)
    ax_t.grid(True, linestyle=":", alpha=0.6)

    n = signal.size
    freqs = np.fft.fftfreq(n, d=1.0 / sample_rate)
    magnitude = np.abs(np.fft.fft(signal)) / (n / 2)
    pos = freqs >= 0
    ax_f.plot(freqs[pos] / 1000, magnitude[pos], "r-", linewidth=0.8)
    ax_f.set_xlabel("Frecuencia (kHz)")
    ax_f.set_ylabel("Magnitud")
    ax_f.set_title("FFT: portadora + bandas laterales", fontsize=10)
    ax_f.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig
