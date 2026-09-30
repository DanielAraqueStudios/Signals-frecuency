"""Synthetic grayscale test image: flat blocks, a hard edge, a gradient and
a fine checkerboard patch, so lowpass/highpass kernels have real content to
act on without needing a real photo (none is available in this repo)."""

import numpy as np


def generar_imagen_sintetica(size: int = 256) -> np.ndarray:
    """Builds a `size x size` uint8 grayscale test image, quadrant layout:

    - top-left: flat mid-gray block
    - top-right: hard-edge step (black / white)
    - bottom-left: smooth horizontal gradient
    - bottom-right: fine high-frequency checkerboard
    """
    half = size // 2
    img = np.zeros((size, size), dtype=np.float64)

    img[0:half, 0:half] = 128.0

    step = np.zeros((half, half), dtype=np.float64)
    step[:, half // 2:] = 255.0
    img[0:half, half:size] = step

    gradient = np.linspace(0, 255, half)
    img[half:size, 0:half] = np.tile(gradient, (half, 1))

    checker_period = 4
    yy, xx = np.meshgrid(np.arange(half), np.arange(half), indexing="ij")
    checker = (((yy // checker_period) + (xx // checker_period)) % 2) * 255.0
    img[half:size, half:size] = checker

    return img.astype(np.uint8)
