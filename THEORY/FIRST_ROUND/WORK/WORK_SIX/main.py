"""CLI entry point for WORK_SIX (Tarea 2):

Parte 1 (wavelet spectrum): CWT energy scalogram of the 'gato' recording.
Parte 1 (vectors): the six correlation vectors slid across the cat audio,
    producing a 100-element output vector.
Parte 2: CWT scalograms of the two available voice recordings
    (persona1, persona2 — see readme.md for why there are only two).

Usage:
    python main.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from wavelet_lab import (
    VECTORS,
    correlation_vector_100,
    cwt_scalogram,
    load_audio,
    plot_correlation_vector,
    plot_scalogram,
)
from wavelet_lab.vectors import _split_counts

ROOT = Path(__file__).parent
AUDIO_DIR = ROOT / "audio_samples"
OUTPUT_DIR = ROOT / "output"


def main(save: bool = True, show: bool = True) -> None:
    """Run both parts of Tarea 2 and render/save all figures.

    Args:
        save: If True, save figures and the 100-element vector to `output/`.
        show: If True, call `plt.show()` (blocks until windows close).
    """
    if save:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Parte 1: wavelet spectrum of the cat audio ---
    cat_signal, cat_sr = load_audio(str(AUDIO_DIR / "gato" / "gato.ogg"))
    print(f"Audio 'gato': {cat_signal.size} muestras @ {cat_sr} Hz")

    energy, freqs, times = cwt_scalogram(cat_signal, cat_sr)
    fig_cat = plot_scalogram(energy, freqs, times, "Espectro wavelet (CWT) — audio 'gato'")
    if save:
        fig_cat.savefig(OUTPUT_DIR / "wavelet_gato.png", dpi=150)

    # --- Parte 1: 100-element correlation output vector ---
    output_vector = correlation_vector_100(cat_signal)
    print(f"Vector de salida (100 posiciones): min={output_vector.min():.4f}, max={output_vector.max():.4f}")
    if save:
        np.save(OUTPUT_DIR / "correlation_vector_100.npy", output_vector)
        np.savetxt(OUTPUT_DIR / "correlation_vector_100.csv", output_vector, delimiter=",")

    counts = _split_counts(len(output_vector), len(VECTORS))
    boundaries = list(np.cumsum(counts))
    fig_vec = plot_correlation_vector(output_vector, boundaries, list(VECTORS.keys()))
    if save:
        fig_vec.savefig(OUTPUT_DIR / "correlation_vector_100.png", dpi=150)

    # --- Parte 2: wavelet scalograms for the available voice recordings ---
    for name in ("persona1", "persona2"):
        signal, sr = load_audio(str(AUDIO_DIR / name / f"{name}.wav"))
        print(f"Audio '{name}': {signal.size} muestras @ {sr} Hz")
        energy, freqs, times = cwt_scalogram(signal, sr)
        fig = plot_scalogram(energy, freqs, times, f"Espectro wavelet (CWT) — {name}")
        if save:
            fig.savefig(OUTPUT_DIR / f"wavelet_{name}.png", dpi=150)

    if show:
        plt.show()


if __name__ == "__main__":
    main()
