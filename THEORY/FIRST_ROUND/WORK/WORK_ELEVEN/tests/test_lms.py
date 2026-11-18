import numpy as np

from lms_lab.lms import run_lms
from lms_lab.signals import sample_times, white_noise
from lms_lab.unknown_system import apply_unknown_system, unknown_fir_coefficients


def test_lms_identifies_unknown_fir_coefficients():
    rng = np.random.default_rng(1)
    t = sample_times(2.0, 2000)
    x = white_noise(len(t), power=1.0, rng=rng)
    h_true = unknown_fir_coefficients()
    d = apply_unknown_system(x, h_true)

    _, _, w_history = run_lms(x, d, n_taps=len(h_true), mu=0.02)

    initial_error = np.linalg.norm(w_history[0] - h_true)
    final_error = np.linalg.norm(w_history[-1] - h_true)

    assert initial_error > 0
    assert final_error < 0.05
    assert final_error < 0.05 * initial_error


def test_lms_output_and_error_shapes():
    rng = np.random.default_rng(2)
    x = white_noise(500, power=1.0, rng=rng)
    d = white_noise(500, power=1.0, rng=rng)
    y, e, w_history = run_lms(x, d, n_taps=4, mu=0.01)

    assert y.shape == (500,)
    assert e.shape == (500,)
    assert w_history.shape == (500, 4)
    np.testing.assert_allclose(e, d - y)


def test_lms_zero_desired_and_input_keeps_weights_at_zero():
    x = np.zeros(100)
    d = np.zeros(100)
    y, e, w_history = run_lms(x, d, n_taps=3, mu=0.1)
    np.testing.assert_allclose(w_history, 0.0)
    np.testing.assert_allclose(y, 0.0)
    np.testing.assert_allclose(e, 0.0)
