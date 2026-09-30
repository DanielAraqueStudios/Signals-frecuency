"""Headless result saving (cod01.py used cv2.imshow/waitKey, no display here)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def guardar_resultado(imagen: np.ndarray, titulo: str, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(imagen, cmap="gray", vmin=0, vmax=255)
    ax.set_title(titulo)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
