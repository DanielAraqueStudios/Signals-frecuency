import numpy as np

from lms_lab.unknown_system import apply_unknown_system, unknown_fir_coefficients


def test_apply_unknown_system_matches_convolution_definition():
    h = unknown_fir_coefficients()
    x = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    y = apply_unknown_system(x, h)
    # Impulse response of an FIR filter is its own coefficients.
    np.testing.assert_allclose(y[: len(h)], h)


def test_apply_unknown_system_output_length_matches_input():
    h = unknown_fir_coefficients()
    x = np.arange(20.0)
    y = apply_unknown_system(x, h)
    assert len(y) == len(x)
