import numpy as np

from lms_lab.lms import run_lms
from lms_lab.signals import sample_times, white_noise
from lms_lab.unknown_system import apply_unknown_system, unknown_fir_coefficients


def _final_weight_error(mu, rng_seed=5):
    rng = np.random.default_rng(rng_seed)
    t = sample_times(2.0, 2000)
    x = white_noise(len(t), power=1.0, rng=rng)
    h_true = unknown_fir_coefficients()
    d = apply_unknown_system(x, h_true)
    _, _, w_history = run_lms(x, d, n_taps=len(h_true), mu=mu)
    return np.linalg.norm(w_history[-1] - h_true)


def test_small_mu_converges_slower_than_moderate_mu():
    # A tiny step size has not nearly converged over the same 4000 samples
    # a moderate one needs to settle -- same input power, same unknown system.
    error_small_mu = _final_weight_error(mu=0.0005)
    error_moderate_mu = _final_weight_error(mu=0.02)
    assert error_small_mu > error_moderate_mu


def test_excessively_large_mu_diverges():
    # mu must stay below 2 / (n_taps * input_power) for stability with a
    # white-noise input of power 1 here; a mu far past that blows up.
    error_large_mu = _final_weight_error(mu=1.5)
    assert not np.isfinite(error_large_mu) or error_large_mu > 10
