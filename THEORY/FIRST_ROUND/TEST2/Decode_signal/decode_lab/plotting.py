"""Headless figure: envelope with symbol boundaries, and the calibration fit."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .symbols import N_CALIBRATION_SYMBOLS, SYMBOL_DURATION_S


def plot_decode(t: np.ndarray, envelope: np.ndarray, symbol_avgs: np.ndarray,
                 slope: float, intercept: float, out_path: str | Path) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(10, 9))

    axes[0].plot(t, envelope, linewidth=0.6)
    axes[0].set_title("Envolvente (magnitud de Hilbert)")
    axes[0].set_xlabel("Tiempo (s)")
    axes[0].set_ylabel("Amplitud")

    symbol_times = (np.arange(len(symbol_avgs)) + 0.5) * SYMBOL_DURATION_S
    axes[1].plot(symbol_times, symbol_avgs, "o-", markersize=3)
    axes[1].axvline(N_CALIBRATION_SYMBOLS * SYMBOL_DURATION_S, color="red",
                     linestyle="--", label="fin calibracion")
    axes[1].set_title("Promedio por simbolo (15 ms)")
    axes[1].set_xlabel("Tiempo (s)")
    axes[1].set_ylabel("Amplitud promedio")
    axes[1].legend()

    cal = symbol_avgs[:N_CALIBRATION_SYMBOLS]
    known = np.arange(N_CALIBRATION_SYMBOLS)
    axes[2].scatter(cal, known, label="rampa de calibracion")
    fit_x = np.linspace(cal.min(), cal.max(), 50)
    axes[2].plot(fit_x, slope * fit_x + intercept, "r--", label="ajuste lineal")
    axes[2].set_title("Calibracion: nivel vs. amplitud promedio")
    axes[2].set_xlabel("Amplitud promedio")
    axes[2].set_ylabel("Nivel (0-15)")
    axes[2].legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
