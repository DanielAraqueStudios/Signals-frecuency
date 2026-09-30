"""Kernel definitions: the three original 5x5 kernels from cod01.py, kept
byte-for-byte identical, plus one new zero-sum kernel for part (b)."""

import numpy as np

# Original kernels, unchanged from TEST2/muestras/cod01.py
kernel_pasa_bajas = np.array([[0.04, 0.04, 0.04, 0.04, 0.04],
                               [0.04, 0.04, 0.04, 0.04, 0.04],
                               [0.04, 0.04, 0.04, 0.04, 0.04],
                               [0.04, 0.04, 0.04, 0.04, 0.04],
                               [0.04, 0.04, 0.04, 0.04, 0.04]])

kernel_pasa_altas00 = np.array([[2, 2, 2, 2, 2],
                                 [2, -3, -3, -3, 2],
                                 [2, -3, -7, -3, 2],
                                 [2, -3, -3, -3, 2],
                                 [2, 2, 2, 2, 2]], dtype=np.float64)

kernel_pasa_altas02 = np.array([[0, 0, 0, 0, 0],
                                 [0, -3, -3, -3, 0],
                                 [0, -3, 24, -3, 0],
                                 [0, -3, -3, -3, 0],
                                 [0, 0, 0, 0, 0]], dtype=np.float64)

# New kernel for part (b): square, values sum to exactly zero (classic
# discrete Laplacian: 8 ring cells at +1, center at -8 -> sum = 0).
kernel_nuevo_suma_cero = np.array([[1, 1, 1],
                                    [1, -8, 1],
                                    [1, 1, 1]], dtype=np.float64)
