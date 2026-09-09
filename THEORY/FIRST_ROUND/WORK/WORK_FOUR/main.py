"""CLI entry point: convolves the 'gato' recording with each kernel in
`conv_lab.KERNELS` and plots input/kernel/output for every one.

Usage:
    python main.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from conv_lab import KERNELS, convolve, load_audio, plot_convolution
from conv_lab.audio import segment

AUDIO_PATH = Path(__file__).parent / "audio_samples" / "gato" / "gato.ogg"
FIGURES_DIR = Path(__file__).parent / "output"

# Segment plotted alongside each kernel: short enough that individual
# samples/the kernel's shape are still visible in a static figure.
SEGMENT_DURATION_S = 0.01
SEGMENT_START_S = 0.5  # skip the first half-second (often near-silent lead-in)


def main(save: bool = True, show: bool = True) -> None:
    """Print numeric results and render one figure per registered kernel.

    Args:
        save: If True, also save each figure to `output/`.
        show: If True, call `plt.show()` (blocks until windows close).
    """
    signal, sample_rate = load_audio(str(AUDIO_PATH))
    x_segment = segment(signal, sample_rate, SEGMENT_DURATION_S, SEGMENT_START_S)
    print(f"Audio: {AUDIO_PATH.name} @ {sample_rate} Hz, segmento de {x_segment.size} muestras")

    if save:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    for name, kernel in KERNELS.items():
        y_segment = convolve(x_segment, kernel, mode="full")
        print(
            f"  {name}: kernel de {kernel.size} muestras -> "
            f"salida de {y_segment.size} muestras "
            f"(min={y_segment.min():.4f}, max={y_segment.max():.4f})"
        )
        fig = plot_convolution(x_segment, kernel, y_segment, title=f"Convolución 'gato' * {name}")
        if save:
            fig.savefig(FIGURES_DIR / f"convolucion_{name}.png", dpi=150)

    if show:
        plt.show()


if __name__ == "__main__":
    main()
