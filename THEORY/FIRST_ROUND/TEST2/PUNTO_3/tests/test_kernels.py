import numpy as np
import pytest

from image_filter_lab.kernels import (
    kernel_nuevo_suma_cero,
    kernel_pasa_altas00,
    kernel_pasa_altas02,
    kernel_pasa_bajas,
)


def test_kernels_square():
    for kernel in (kernel_pasa_bajas, kernel_pasa_altas00, kernel_pasa_altas02, kernel_nuevo_suma_cero):
        assert kernel.shape[0] == kernel.shape[1]


def test_kernel_pasa_bajas_sum_is_one():
    assert kernel_pasa_bajas.sum() == pytest.approx(1.0, abs=1e-9)


def test_kernel_pasa_altas00_actual_sum():
    # Reports the real computed sum rather than assuming it is zero.
    assert kernel_pasa_altas00.sum() == pytest.approx(1.0, abs=1e-9)


def test_kernel_pasa_altas02_actual_sum():
    assert kernel_pasa_altas02.sum() == pytest.approx(0.0, abs=1e-9)


def test_kernel_nuevo_suma_cero_is_zero():
    assert kernel_nuevo_suma_cero.sum() == pytest.approx(0.0, abs=1e-9)
