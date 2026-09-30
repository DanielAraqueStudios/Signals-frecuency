"""Figure generation for Punto 2 (a)(b), separated from computation."""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np


def plot_filtered_at_bit_rate(t, raw, fir_out, iir_out, out_path: str) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(t, raw, linewidth=0.5)
    axes[0].set_title("Señal original (OOK)")
    axes[1].plot(t, fir_out, linewidth=0.7, color="tab:orange")
    axes[1].set_title("FIR orden 50 @ frecuencia de bit (1/T)")
    axes[2].plot(t, iir_out, linewidth=0.7, color="tab:green")
    axes[2].set_title("IIR Butterworth orden < 10 @ frecuencia de bit (1/T)")
    axes[2].set_xlabel("Tiempo (s)")
    for ax in axes:
        ax.set_ylabel("Amplitud")
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def plot_spectrum(freqs, magnitude, bit_rate_hz, carrier_hz, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(freqs, magnitude, linewidth=0.7)
    ax.axvline(bit_rate_hz, color="tab:red", linestyle="--", label=f"1/T = {bit_rate_hz:.0f} Hz")
    ax.axvline(carrier_hz, color="tab:green", linestyle="--", label=f"portadora ~ {carrier_hz:.0f} Hz")
    ax.set_xlim(0, carrier_hz * 3)
    ax.set_xlabel("Frecuencia (Hz)")
    ax.set_ylabel("Magnitud")
    ax.set_title("Espectro de la señal OOK")
    ax.legend()
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def plot_hilbert_and_bits(t, raw, envelope, square_wave, out_path: str) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(t, raw, linewidth=0.5)
    axes[0].set_title("Señal original")
    axes[1].plot(t, envelope, linewidth=0.7, color="tab:orange")
    axes[1].set_title("Magnitud de la transformada de Hilbert")
    axes[2].plot(t, square_wave, linewidth=1.0, color="tab:green")
    axes[2].set_title("Señal cuadrada reconstruida (bits)")
    axes[2].set_xlabel("Tiempo (s)")
    axes[2].set_ylim(-0.2, 1.2)
    for ax in axes[:2]:
        ax.set_ylabel("Amplitud")
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
