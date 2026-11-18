"""Matplotlib figure assembly for the LMS adaptive-filter exercises."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def plot_weight_convergence(
    w_history: np.ndarray, true_coefficients: np.ndarray, title: str
) -> plt.Figure:
    """Each adaptive tap's trajectory over time vs. its true target value."""
    n_samples, n_taps = w_history.shape
    fig, ax = plt.subplots(figsize=(11, 5))
    colors = plt.cm.tab10(np.linspace(0, 1, n_taps))
    for k in range(n_taps):
        ax.plot(w_history[:, k], color=colors[k], linewidth=1.2, label=f"w[{k}]")
        ax.axhline(true_coefficients[k], color=colors[k], linewidth=0.8, linestyle=":")
    ax.set_title(title)
    ax.set_xlabel("Muestra n")
    ax.set_ylabel("Valor del peso")
    ax.legend(ncol=n_taps, fontsize=8)
    ax.grid(True, linestyle=":")
    fig.tight_layout()
    return fig


def plot_identification_error(e: np.ndarray, title: str) -> plt.Figure:
    """Instantaneous error e[n] and its squared value on a log scale."""
    fig, axes = plt.subplots(2, 1, figsize=(11, 7))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    axes[0].plot(e, color="tab:red", linewidth=0.8)
    axes[0].set_title("Error instantáneo e[n]")
    axes[0].set_xlabel("Muestra n")
    axes[0].set_ylabel("e[n]")
    axes[0].grid(True, linestyle=":")

    axes[1].semilogy(e**2 + 1e-18, color="tab:purple", linewidth=0.8)
    axes[1].set_title("Error cuadrático e[n]^2 (escala log)")
    axes[1].set_xlabel("Muestra n")
    axes[1].set_ylabel("e[n]^2")
    axes[1].grid(True, linestyle=":", which="both")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def plot_noise_cancellation(
    t: np.ndarray,
    clean: np.ndarray,
    noisy: np.ndarray,
    recovered: np.ndarray,
    title: str,
    time_unit: str = "s",
) -> plt.Figure:
    """Clean reference vs. noisy observation vs. LMS-recovered signal."""
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    fig.suptitle(title, fontsize=14, fontweight="bold")

    axes[0].plot(t, clean, color="tab:green", linewidth=0.9)
    axes[0].set_title("Señal limpia (referencia)")
    axes[0].grid(True, linestyle=":")

    axes[1].plot(t, noisy, color="tab:gray", linewidth=0.7)
    axes[1].set_title("Señal con ruido añadido")
    axes[1].grid(True, linestyle=":")

    axes[2].plot(t, recovered, color="tab:blue", linewidth=0.9)
    axes[2].set_title("Salida LMS (ruido estimado y restado)")
    axes[2].set_xlabel(f"Tiempo ({time_unit})")
    axes[2].grid(True, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def plot_mu_sweep(
    mse_curves: dict[float, np.ndarray],
    final_mse: dict[float, float],
    title: str,
) -> plt.Figure:
    """Learning curves (MSE vs. n) and final-error-vs-mu summary, across a
    sweep of step sizes -- some stable/slow, some fast, some diverging.
    """
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    for mu, mse in mse_curves.items():
        axes[0].semilogy(mse + 1e-18, linewidth=1.1, label=f"mu = {mu:g}")
    axes[0].set_title("Curvas de aprendizaje (MSE vs. n)")
    axes[0].set_xlabel("Muestra n")
    axes[0].set_ylabel("MSE (promedio móvil)")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, linestyle=":", which="both")

    mus = sorted(final_mse.keys())
    finals = [final_mse[m] for m in mus]
    axes[1].semilogy(mus, finals, "o-", color="tab:red")
    axes[1].set_title("Error final vs. mu")
    axes[1].set_xlabel("mu")
    axes[1].set_ylabel("MSE final (últimas muestras)")
    axes[1].grid(True, linestyle=":", which="both")

    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return fig
