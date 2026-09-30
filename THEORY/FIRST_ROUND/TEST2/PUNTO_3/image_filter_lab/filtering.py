"""Kernel application via cv2.filter2D — same call cod01.py makes."""

import cv2
import numpy as np


def aplicar_kernel(imagen: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    return cv2.filter2D(imagen, -1, kernel)


def aplicar_cascada_pasa_bandas(imagen: np.ndarray, kernel_bajas: np.ndarray,
                                 kernel_altas: np.ndarray) -> np.ndarray:
    """Lowpass then highpass, mirroring cod01.py's "Filtro Pasa Bandas" block."""
    filtrada = cv2.filter2D(imagen, -1, kernel_bajas)
    filtrada = cv2.filter2D(filtrada, -1, kernel_altas)
    return filtrada
