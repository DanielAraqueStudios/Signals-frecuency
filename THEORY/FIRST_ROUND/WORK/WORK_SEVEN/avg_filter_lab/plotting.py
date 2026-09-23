"""Before/after time-domain and FFT plots for moving-average filtering."""

from __future__ import annotations

import matplotlib.pyplot as plt

from .spectrum import single_sided_fft


def plot_filter_comparison(
    t,
    before,
    after,
    sample_rate: float,
    cutoff_hz: float,
    window: int,
    title: str,
    max_freq_hz: float | None = None,
):
    """Assemble a 2x2 figure: time-domain and FFT, before vs. after filtering.

    Args:
        t: Time axis (seconds), matching `before`/`after`.
        before: Signal before filtering.
        after: Signal after the moving-average filter.
        sample_rate: Sampling rate (Hz), used for the FFTs.
        cutoff_hz: Target -3dB cutoff used to size the filter (for the title).
        window: Moving-average window length used (for the title).
        title: Overall figure title (signal name).
        max_freq_hz: If given, FFT subplots are cropped to this frequency.

    Returns:
        The assembled (not shown/saved) `matplotlib.figure.Figure`.
    """
    freqs_before, mag_before = single_sided_fft(before, sample_rate, max_freq_hz=max_freq_hz)
    freqs_after, mag_after = single_sided_fft(after, sample_rate, max_freq_hz=max_freq_hz)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    axes[0, 0].plot(t * 1000, before, color="tab:blue", linewidth=0.8)
    axes[0, 0].set_title("Antes (dominio del tiempo)")
    axes[0, 0].set_xlabel("Tiempo (ms)")
    axes[0, 0].set_ylabel("Amplitud")
    axes[0, 0].grid(True, linestyle=":")

    axes[0, 1].plot(t * 1000, after, color="tab:red", linewidth=0.8)
    axes[0, 1].set_title(f"Despues (fc = {cutoff_hz} Hz, N = {window})")
    axes[0, 1].set_xlabel("Tiempo (ms)")
    axes[0, 1].set_ylabel("Amplitud")
    axes[0, 1].grid(True, linestyle=":")

    axes[1, 0].stem(freqs_before, mag_before, linefmt="b-", markerfmt="bo", basefmt="k-")
    axes[1, 0].set_title("FFT antes")
    axes[1, 0].set_xlabel("Frecuencia (Hz)")
    axes[1, 0].set_ylabel("Magnitud")
    axes[1, 0].grid(True, linestyle=":")

    axes[1, 1].stem(freqs_after, mag_after, linefmt="r-", markerfmt="ro", basefmt="k-")
    axes[1, 1].set_title("FFT despues")
    axes[1, 1].set_xlabel("Frecuencia (Hz)")
    axes[1, 1].set_ylabel("Magnitud")
    axes[1, 1].grid(True, linestyle=":")

    fig.suptitle(title)
    fig.tight_layout()
    return fig
