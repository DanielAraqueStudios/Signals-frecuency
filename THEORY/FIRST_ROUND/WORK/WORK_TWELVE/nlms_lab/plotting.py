"""Matplotlib figure assembly for the NLMS system-ID, ANC, and LMS-comparison tasks."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def plot_system_identification(
    true_coeffs: np.ndarray,
    weights_history: np.ndarray,
    error: np.ndarray,
    title: str,
) -> plt.Figure:
    """Weight convergence toward the unknown FIR coefficients + error curve."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    n_taps = true_coeffs.size
    for tap in range(n_taps):
        axes[0].plot(weights_history[:, tap], linewidth=1.0, label=f"w[{tap}]")
        axes[0].axhline(true_coeffs[tap], color="black", linewidth=0.8, linestyle="--")
    axes[0].set_xlabel("Iteración")
    axes[0].set_ylabel("Valor del coeficiente")
    axes[0].set_title("Pesos adaptados vs. coeficientes reales (líneas punteadas)")
    axes[0].legend(fontsize=8, ncol=2)
    axes[0].grid(True, linestyle=":")

    axes[1].plot(np.abs(error), color="tab:red", linewidth=0.8)
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Iteración")
    axes[1].set_ylabel("|error| (escala log)")
    axes[1].set_title("Error de predicción a-priori")
    axes[1].grid(True, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


def plot_noise_cancellation(
    t: np.ndarray,
    clean: np.ndarray,
    noisy: np.ndarray,
    recovered: np.ndarray,
    title: str,
    time_unit: str = "s",
) -> plt.Figure:
    """Clean reference, noisy observation, and NLMS-recovered signal."""
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    fig.suptitle(title, fontsize=14, fontweight="bold")

    axes[0].plot(t, clean, color="tab:green", linewidth=0.9)
    axes[0].set_title("Señal limpia (referencia)")
    axes[0].grid(True, linestyle=":")

    axes[1].plot(t, noisy, color="tab:gray", linewidth=0.7, alpha=0.8)
    axes[1].set_title("Señal observada (con ruido)")
    axes[1].grid(True, linestyle=":")

    axes[2].plot(t, recovered, color="tab:blue", linewidth=0.9)
    axes[2].set_title("Señal recuperada por NLMS")
    axes[2].set_xlabel(f"Tiempo ({time_unit})")
    axes[2].grid(True, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def plot_nlms_vs_lms_varying_power(
    signal_power_profile: np.ndarray,
    nlms_error: np.ndarray,
    lms_error: np.ndarray,
    power_step_index: int,
    title: str,
) -> plt.Figure:
    """NLMS vs. plain-LMS convergence under a step change in input power."""
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    fig.suptitle(title, fontsize=14, fontweight="bold")

    axes[0].plot(signal_power_profile, color="black", linewidth=1.0)
    axes[0].axvline(power_step_index, color="gray", linestyle=":", linewidth=1.0)
    axes[0].set_title("Amplitud instantánea de la entrada (escalón de potencia)")
    axes[0].grid(True, linestyle=":")

    axes[1].plot(np.abs(nlms_error), color="tab:blue", linewidth=0.8, label="NLMS")
    axes[1].plot(np.abs(lms_error), color="tab:red", linewidth=0.8, label="LMS (mu fijo)")
    axes[1].axvline(power_step_index, color="gray", linestyle=":", linewidth=1.0)
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Iteración")
    axes[1].set_ylabel("|error| (escala log)")
    axes[1].set_title("Error de predicción: NLMS vs. LMS")
    axes[1].legend()
    axes[1].grid(True, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig
