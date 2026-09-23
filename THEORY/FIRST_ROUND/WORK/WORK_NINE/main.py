"""CLI entry point: AM-modulates the 'gato' recording at 50 kHz and 500 kHz.

Usage:
    python main.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from modulation_lab import CARRIER_FREQ_HZ, load_audio, modulate_at_rate, plot_modulation

AUDIO_PATH = Path(__file__).parent / "audio_samples" / "gato" / "gato.ogg"
FIGURES_DIR = Path(__file__).parent / "output"

TARGET_SAMPLE_RATES = (50_000, 500_000)


def main(save: bool = True, show: bool = True) -> None:
    """Modulate the cat recording at each target rate and plot the result.

    Args:
        save: If True, also save each figure to `output/`.
        show: If True, call `plt.show()` (blocks until windows close).
    """
    signal, orig_sr = load_audio(str(AUDIO_PATH))
    print(f"Audio: {AUDIO_PATH.name} @ {orig_sr} Hz, {signal.size} muestras, portadora = {CARRIER_FREQ_HZ:.0f} Hz")

    if save:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    for target_fs in TARGET_SAMPLE_RATES:
        modulated = modulate_at_rate(signal, orig_sr, target_fs)
        print(f"  fs={target_fs} Hz -> {modulated.size} muestras (min={modulated.min():.4f}, max={modulated.max():.4f})")

        fig = plot_modulation(modulated, target_fs, title=f"AM 'gato' @ fs={target_fs / 1000:.0f} kHz")
        if save:
            fig.savefig(FIGURES_DIR / f"modulacion_{target_fs}hz.png", dpi=150)

    if show:
        plt.show()


if __name__ == "__main__":
    main()
