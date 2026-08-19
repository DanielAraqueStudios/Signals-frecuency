"""Generate the item-8 report figures (gato/perro/gallo) from real audio.

Loads each recording in `audio_samples/<categoria>/`, runs the real
`animal_analyzer.core.analyze_audio` pipeline (3s window, FFT, mean, std,
dominant frequency), renders a clean (print-friendly, light background)
time+FFT figure per animal plus a comparison figure, and prints the
computed statistics and pairwise separability scores so the LaTeX report
can be updated with real numbers instead of placeholder ones.

Usage:
    python scripts/generate_animal_figures.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from animal_analyzer.core import analyze_audio, compare_categories, load_audio

FILES = {
    "Gato": "audio_samples/gato/gato.ogg",
    "Perro": "audio_samples/perro/perro.ogg",
    "Gallo": "audio_samples/gallo/gallo.ogg",
}
OUT_DIR = "report/figuras"
FILENAMES = {"Gato": "gato.png", "Perro": "perro.png", "Gallo": "gallo.png"}
COLORS = {"Gato": "tab:blue", "Perro": "tab:orange", "Gallo": "tab:green"}


def plot_single(name: str, result: dict) -> None:
    """Render and save the time-domain + FFT figure for one recording."""
    windowed = result["windowed_signal"]
    fs = result["sample_rate"]
    t = [i / fs for i in range(len(windowed))]
    limit = min(10_000, fs / 2)
    mask = result["frequencies"] <= limit

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6))
    fig.suptitle(f"{name}: señal y espectro (ventana analizada = {len(windowed) / fs:.2f} s)", fontweight="bold")

    ax1.plot(t, windowed, linewidth=0.7, color=COLORS[name])
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("Amplitud")
    ax1.set_title("Dominio del tiempo")
    ax1.grid(True, linestyle=":", alpha=0.5)

    ax2.plot(result["frequencies"][mask], result["magnitude"][mask], linewidth=0.9, color=COLORS[name])
    ax2.axvline(result["dominant_frequency_hz"], color="red", linestyle="--", linewidth=1,
                label=f"Dominante: {result['dominant_frequency_hz']:.1f} Hz")
    ax2.set_xlabel("Frecuencia (Hz)")
    ax2.set_ylabel("Magnitud")
    ax2.set_title("Espectro (FFT)")
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.legend()

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(OUT_DIR, FILENAMES[name]), dpi=150)
    plt.close(fig)


def plot_comparison(results: dict[str, dict]) -> None:
    """Render and save the overlaid FFT comparison figure."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for name, result in results.items():
        limit = min(10_000, result["sample_rate"] / 2)
        mask = result["frequencies"] <= limit
        ax.plot(result["frequencies"][mask], result["magnitude"][mask], linewidth=1, label=name, color=COLORS[name])
        ax.axvline(result["dominant_frequency_hz"], color=COLORS[name], linestyle=":", linewidth=1, alpha=0.7)

    ax.set_xlabel("Frecuencia (Hz)")
    ax.set_ylabel("Magnitud")
    ax.set_title("Comparación de espectros: Gato vs. Perro vs. Gallo")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend()

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "animales_comparacion.png"), dpi=150)
    plt.close(fig)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    results = {}
    for name, path in FILES.items():
        signal, fs = load_audio(path)
        result = analyze_audio(signal, fs)
        results[name] = result
        plot_single(name, result)
        print(
            f"{name}: fs={fs} Hz, duracion_total={len(signal) / fs:.3f} s, "
            f"ventana_analizada={len(result['windowed_signal']) / fs:.3f} s, "
            f"media={result['mean']:.6f}, std={result['std']:.6f}, "
            f"f_dominante={result['dominant_frequency_hz']:.2f} Hz"
        )

    plot_comparison(results)
    print()
    print(compare_categories(results))


if __name__ == "__main__":
    main()
