"""Generate every item-8 report figure from real (or synthesized) audio.

Loads each recording in `audio_samples/<categoria>/`, runs the real
`animal_analyzer.core.analyze_audio` pipeline (3s window, FFT, mean, std,
dominant frequency) for every category (animals, instruments, voices),
renders a clean (print-friendly, light background) time+FFT figure per
recording plus one comparison figure per group, and prints the computed
statistics and pairwise separability scores so the LaTeX report can be
updated with real numbers instead of placeholder ones.

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

OUT_DIR = "report/figuras"

GROUPS = {
    "animales": {
        "files": {
            "Gato": "audio_samples/gato/gato.ogg",
            "Perro": "audio_samples/perro/perro.ogg",
            "Gallo": "audio_samples/gallo/gallo.ogg",
        },
        "filenames": {"Gato": "gato.png", "Perro": "perro.png", "Gallo": "gallo.png"},
        "colors": {"Gato": "tab:blue", "Perro": "tab:orange", "Gallo": "tab:green"},
        "comparison_file": "animales_comparacion.png",
        "comparison_title": "Comparación de espectros: Gato vs. Perro vs. Gallo",
    },
    "instrumentos": {
        "files": {
            "Contrabajo": "audio_samples/contrabajo/contrabajo.oga",
            "Piano": "audio_samples/piano/piano.ogg",
            "Flauta": "audio_samples/flauta/flauta.ogg",
        },
        "filenames": {"Contrabajo": "contrabajo.png", "Piano": "piano.png", "Flauta": "flauta.png"},
        "colors": {"Contrabajo": "tab:brown", "Piano": "tab:purple", "Flauta": "tab:cyan"},
        "comparison_file": "instrumentos_comparacion.png",
        "comparison_title": "Comparación de espectros: Contrabajo vs. Piano vs. Flauta",
    },
    "voces": {
        "files": {
            "Persona 1": "audio_samples/persona1/persona1.wav",
            "Persona 2": "audio_samples/persona2/persona2.wav",
        },
        "filenames": {"Persona 1": "persona1.png", "Persona 2": "persona2.png"},
        "colors": {"Persona 1": "tab:red", "Persona 2": "tab:gray"},
        "comparison_file": "personas_comparacion.png",
        "comparison_title": "Comparación de espectros: Persona 1 vs. Persona 2",
    },
}


def plot_single(name: str, result: dict, filename: str, color: str) -> None:
    """Render and save the time-domain + FFT figure for one recording."""
    windowed = result["windowed_signal"]
    fs = result["sample_rate"]
    t = [i / fs for i in range(len(windowed))]
    limit = min(10_000, fs / 2)
    mask = result["frequencies"] <= limit

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6))
    fig.suptitle(f"{name}: señal y espectro (ventana analizada = {len(windowed) / fs:.2f} s)", fontweight="bold")

    ax1.plot(t, windowed, linewidth=0.7, color=color)
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("Amplitud")
    ax1.set_title("Dominio del tiempo")
    ax1.grid(True, linestyle=":", alpha=0.5)

    ax2.plot(result["frequencies"][mask], result["magnitude"][mask], linewidth=0.9, color=color)
    ax2.axvline(result["dominant_frequency_hz"], color="red", linestyle="--", linewidth=1,
                label=f"Dominante: {result['dominant_frequency_hz']:.1f} Hz")
    ax2.set_xlabel("Frecuencia (Hz)")
    ax2.set_ylabel("Magnitud")
    ax2.set_title("Espectro (FFT)")
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.legend()

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(OUT_DIR, filename), dpi=150)
    plt.close(fig)


def plot_comparison(results: dict[str, dict], colors: dict[str, str], filename: str, title: str) -> None:
    """Render and save the overlaid FFT comparison figure for a group."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for name, result in results.items():
        limit = min(10_000, result["sample_rate"] / 2)
        mask = result["frequencies"] <= limit
        ax.plot(result["frequencies"][mask], result["magnitude"][mask], linewidth=1, label=name, color=colors[name])
        ax.axvline(result["dominant_frequency_hz"], color=colors[name], linestyle=":", linewidth=1, alpha=0.7)

    ax.set_xlabel("Frecuencia (Hz)")
    ax.set_ylabel("Magnitud")
    ax.set_title(title)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend()

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, filename), dpi=150)
    plt.close(fig)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    for group_name, group in GROUPS.items():
        print(f"=== {group_name} ===")
        results = {}
        for name, path in group["files"].items():
            signal, fs = load_audio(path)
            result = analyze_audio(signal, fs)
            results[name] = result
            plot_single(name, result, group["filenames"][name], group["colors"][name])
            print(
                f"{name}: fs={fs} Hz, duracion_total={len(signal) / fs:.3f} s, "
                f"ventana_analizada={len(result['windowed_signal']) / fs:.3f} s, "
                f"media={result['mean']:.6f}, std={result['std']:.6f}, "
                f"f_dominante={result['dominant_frequency_hz']:.2f} Hz"
            )

        plot_comparison(results, group["colors"], group["comparison_file"], group["comparison_title"])
        print()
        print(compare_categories(results))
        print()


if __name__ == "__main__":
    main()
