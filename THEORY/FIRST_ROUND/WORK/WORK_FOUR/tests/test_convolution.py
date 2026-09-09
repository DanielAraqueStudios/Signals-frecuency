import numpy as np
import pytest

from conv_lab.convolution import convolve, manual_convolve
from conv_lab.kernels import KERNELS, step_kernel


def test_manual_convolve_matches_numpy_for_step_10():
    x = np.arange(1.0, 21.0)  # [1, 2, ..., 20]
    h = step_kernel(10)
    np.testing.assert_allclose(manual_convolve(x, h), np.convolve(x, h))


def test_manual_convolve_matches_numpy_for_step_100():
    rng = np.random.default_rng(0)
    x = rng.normal(size=300)
    h = step_kernel(100)
    np.testing.assert_allclose(manual_convolve(x, h), np.convolve(x, h))


def test_manual_convolve_matches_numpy_for_trapezoid():
    rng = np.random.default_rng(1)
    x = rng.normal(size=50)
    h = KERNELS["trapezoid_10"]
    np.testing.assert_allclose(manual_convolve(x, h), np.convolve(x, h))


def test_convolve_full_length():
    x = np.ones(5)
    h = np.ones(3)
    y = convolve(x, h, mode="full")
    assert y.size == 5 + 3 - 1


def test_convolve_same_length():
    x = np.ones(5)
    h = np.ones(3)
    y = convolve(x, h, mode="same")
    assert y.size == 5


def test_step_kernel_is_a_delayed_moving_sum():
    # h = [0]*5 + [1]*5 => y[n] = x[n-5] + x[n-6] + ... + x[n-9]:
    # a 5-sample boxcar (moving-sum) filter, delayed by 5 samples.
    x = np.array([0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0])
    h = step_kernel(10)
    y = convolve(x, h, mode="full")
    # The single impulse at x[5] should appear, spread across 5 taps,
    # starting at output index 5 (h's first nonzero tap) + 5 (impulse
    # position) = 10.
    nonzero = np.flatnonzero(y)
    assert nonzero.min() == 10
    assert nonzero.max() == 14
    np.testing.assert_allclose(y[10:15], 1.0)


def test_convolve_rejects_empty_input():
    with pytest.raises(ValueError):
        convolve(np.array([]), np.ones(3))
    with pytest.raises(ValueError):
        convolve(np.ones(3), np.array([]))
