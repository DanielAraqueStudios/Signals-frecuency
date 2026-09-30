import numpy as np

from image_filter_lab.generar_imagen import generar_imagen_sintetica


def test_shape_and_dtype():
    img = generar_imagen_sintetica(256)
    assert img.shape == (256, 256)
    assert img.dtype == np.uint8


def test_value_range():
    img = generar_imagen_sintetica(256)
    assert img.min() >= 0
    assert img.max() <= 255


def test_quadrants_differ():
    img = generar_imagen_sintetica(256)
    flat_block = img[0:128, 0:128]
    checker_block = img[128:256, 128:256]
    # A flat block has ~zero variance; the checkerboard has high variance.
    assert flat_block.std() < 1.0
    assert checker_block.std() > 50.0
