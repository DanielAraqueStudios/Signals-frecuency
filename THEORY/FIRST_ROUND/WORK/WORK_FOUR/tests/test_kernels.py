import numpy as np
import pytest

from conv_lab.kernels import KERNELS, TRAPEZOID_10, step_kernel


def test_step_kernel_10():
    np.testing.assert_array_equal(step_kernel(10), [0, 0, 0, 0, 0, 1, 1, 1, 1, 1])


def test_step_kernel_100_is_half_and_half():
    kernel = step_kernel(100)
    assert kernel.size == 100
    assert np.all(kernel[:50] == 0)
    assert np.all(kernel[50:] == 1)


def test_step_kernel_odd_size_gives_extra_to_ones():
    kernel = step_kernel(11)
    assert kernel.size == 11
    assert np.sum(kernel == 0) == 5
    assert np.sum(kernel == 1) == 6


def test_step_kernel_rejects_non_positive_size():
    with pytest.raises(ValueError):
        step_kernel(0)


def test_trapezoid_10_is_symmetric():
    np.testing.assert_allclose(TRAPEZOID_10, TRAPEZOID_10[::-1])
    assert TRAPEZOID_10.max() == 1.0
    assert TRAPEZOID_10.min() == 0.0


def test_registry_contains_all_three_kernels():
    assert set(KERNELS) == {"step_10", "step_100", "trapezoid_10"}
    assert KERNELS["step_10"].size == 10
    assert KERNELS["step_100"].size == 100
    assert KERNELS["trapezoid_10"].size == 10
