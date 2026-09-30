import numpy as np

from image_filter_lab.filtering import aplicar_cascada_pasa_bandas, aplicar_kernel
from image_filter_lab.generar_imagen import generar_imagen_sintetica
from image_filter_lab.kernels import kernel_nuevo_suma_cero, kernel_pasa_altas02, kernel_pasa_bajas


def test_filter2d_output_shape_matches_input():
    imagen = generar_imagen_sintetica(64)
    salida = aplicar_kernel(imagen, kernel_pasa_bajas)
    assert salida.shape == imagen.shape


def test_cascada_output_shape_matches_input():
    imagen = generar_imagen_sintetica(64)
    salida = aplicar_cascada_pasa_bandas(imagen, kernel_pasa_bajas, kernel_pasa_altas02)
    assert salida.shape == imagen.shape


def test_kernel_nuevo_flat_region_near_zero():
    flat = np.full((32, 32), 128, dtype=np.uint8)
    salida = aplicar_kernel(flat, kernel_nuevo_suma_cero)
    interior = salida[4:-4, 4:-4].astype(np.int16)
    assert np.abs(interior).max() <= 2


def test_kernel_nuevo_edge_nontrivial():
    edge = np.zeros((32, 32), dtype=np.uint8)
    edge[:, 16:] = 255
    salida = aplicar_kernel(edge, kernel_nuevo_suma_cero).astype(np.int16)
    assert np.abs(salida).max() > 20
