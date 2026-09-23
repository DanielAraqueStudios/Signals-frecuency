import numpy as np
import pytest
from scipy.signal import butter, lfilter

from filter_lab.apply import apply_cascade, apply_difference_equation
from filter_lab.coefficients import (
    SQRT2,
    biquad_butterworth_bilinear,
    combine_sections,
    order4_manual_sections,
)
from filter_lab.signals import generate_test_signal

FS = 10**5


@pytest.mark.parametrize("fc", [40.0, 100.0])
def test_biquad_dc_gain_is_unity(fc):
    b, a = biquad_butterworth_bilinear(fc, FS)
    dc_gain = np.sum(b) / np.sum(a)
    assert dc_gain == pytest.approx(1.0, abs=1e-9)


def test_biquad_matches_scipy_coefficients():
    # Same math, both a bilinear-transformed Butterworth biquad: the
    # hand-derived closed form should reproduce scipy's design exactly.
    fc = 100.0
    b_manual, a_manual = biquad_butterworth_bilinear(fc, FS, damping=SQRT2)
    b_scipy, a_scipy = butter(2, fc, btype="low", fs=FS)
    np.testing.assert_allclose(b_manual, b_scipy, atol=1e-10)
    np.testing.assert_allclose(a_manual, a_scipy, atol=1e-10)


@pytest.mark.parametrize("fc", [40.0, 100.0])
def test_manual_loop_matches_lfilter_same_coefficients(fc):
    # Core correctness check for the for-loop implementation: given
    # IDENTICAL (b, a), it must agree with scipy.signal.lfilter.
    b, a = biquad_butterworth_bilinear(fc, FS)
    _, x = generate_test_signal(fs=FS)
    y_manual = apply_difference_equation(b, a, x)
    y_scipy = lfilter(b, a, x)
    np.testing.assert_allclose(y_manual, y_scipy, atol=1e-8)


def test_order4_cascade_matches_scipy_butter_design():
    fc = 100.0
    sections = order4_manual_sections(fc, FS)
    b_manual, a_manual = combine_sections(sections)
    b_scipy, a_scipy = butter(4, fc, btype="low", fs=FS)
    np.testing.assert_allclose(b_manual, b_scipy, atol=1e-8)
    np.testing.assert_allclose(a_manual, a_scipy, atol=1e-8)


def test_order4_manual_loop_matches_lfilter_same_coefficients():
    fc = 100.0
    sections = order4_manual_sections(fc, FS)
    b_combined, a_combined = combine_sections(sections)
    _, x = generate_test_signal(fs=FS)

    y_manual_direct = apply_difference_equation(b_combined, a_combined, x)
    y_scipy_direct = lfilter(b_combined, a_combined, x)
    np.testing.assert_allclose(y_manual_direct, y_scipy_direct, atol=1e-6)


def test_order4_cascade_application_matches_combined_direct_form():
    # Applying the two biquads in series (what main.py does) should equal
    # applying the single combined 4th-order system.
    fc = 100.0
    sections = order4_manual_sections(fc, FS)
    b_combined, a_combined = combine_sections(sections)
    _, x = generate_test_signal(fs=FS)

    y_cascade = apply_cascade(sections, x)
    y_direct = apply_difference_equation(b_combined, a_combined, x)
    np.testing.assert_allclose(y_cascade, y_direct, atol=1e-6)


def test_difference_equation_rejects_zero_a0():
    with pytest.raises(ValueError):
        apply_difference_equation(np.array([1.0]), np.array([0.0, 1.0]), np.ones(5))
