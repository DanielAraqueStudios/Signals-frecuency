import numpy as np

from nlms_lab.adaptive import lms_filter, nlms_filter
from nlms_lab.signals import varying_power_signal


def test_nlms_identifies_unknown_fir_coefficients():
    rng = np.random.default_rng(1)
    true_coeffs = np.array([0.8, -0.4, 0.25, -0.1, 0.05])
    n_samples = 4000
    x = rng.standard_normal(n_samples)
    d = np.convolve(x, true_coeffs)[:n_samples]

    weights_history, _, _ = nlms_filter(x, d, filter_order=true_coeffs.size, mu=0.5)

    assert np.allclose(weights_history[-1], true_coeffs, atol=1e-2)


def test_nlms_weight_error_shrinks_substantially():
    rng = np.random.default_rng(2)
    true_coeffs = np.array([1.0, -0.5, 0.3])
    n_samples = 3000
    x = rng.standard_normal(n_samples)
    d = np.convolve(x, true_coeffs)[:n_samples]

    weights_history, _, _ = nlms_filter(x, d, filter_order=true_coeffs.size, mu=0.5)

    initial_error = np.linalg.norm(weights_history[0] - true_coeffs)
    final_error = np.linalg.norm(weights_history[-1] - true_coeffs)
    assert final_error < 0.01 * initial_error


def test_nlms_recovers_clean_tone_from_noisy_observation():
    rng = np.random.default_rng(3)
    fs = 10_000
    t = np.arange(10_000) / fs
    clean = np.sin(2 * np.pi * 60 * t)
    noisy = clean + 0.5 * rng.standard_normal(clean.size)

    _, recovered, _ = nlms_filter(noisy, clean, filter_order=16, mu=0.5)

    steady = slice(len(recovered) // 2, None)
    noisy_rms_error = np.sqrt(np.mean((noisy[steady] - clean[steady]) ** 2))
    recovered_rms_error = np.sqrt(np.mean((recovered[steady] - clean[steady]) ** 2))
    assert recovered_rms_error < 0.5 * noisy_rms_error


def test_nlms_update_step_shrinks_error_each_iteration_on_average():
    rng = np.random.default_rng(4)
    true_coeffs = np.array([0.6, 0.2])
    n_samples = 2000
    x = rng.standard_normal(n_samples)
    d = np.convolve(x, true_coeffs)[:n_samples]

    _, _, error = nlms_filter(x, d, filter_order=true_coeffs.size, mu=0.5)

    first_quarter_energy = np.mean(error[: n_samples // 4] ** 2)
    last_quarter_energy = np.mean(error[-n_samples // 4 :] ** 2)
    assert last_quarter_energy < 0.01 * first_quarter_energy


def test_nlms_converges_more_consistently_than_lms_under_varying_power():
    """Core claim of the readme's non-stationary-power comparison: with a
    single fixed mu that must stay stable at the high-power segment, plain
    LMS's low-power-segment error (relative to LMS's own high-power error)
    is much worse than NLMS's equivalent ratio, because NLMS's step size is
    normalized by instantaneous input energy and LMS's is not.
    """
    rng = np.random.default_rng(5)
    true_coeffs = np.array([0.8, -0.4, 0.25, -0.1, 0.05])
    n_samples = 6000
    low_amplitude, high_amplitude = 0.05, 2.0
    step_index = n_samples // 2

    x = varying_power_signal(n_samples, low_amplitude, high_amplitude, rng)
    d = np.convolve(x, true_coeffs)[:n_samples]

    fixed_mu = 0.05
    _, _, error_nlms = nlms_filter(x, d, filter_order=true_coeffs.size, mu=0.5)
    _, _, error_lms = lms_filter(x, d, filter_order=true_coeffs.size, mu=fixed_mu)

    def late_segment_rms(error, lo, hi):
        segment = error[lo:hi]
        tail = segment[len(segment) // 2 :]
        return np.sqrt(np.mean(tail ** 2))

    nlms_low_rms = late_segment_rms(error_nlms, 0, step_index)
    nlms_high_rms = late_segment_rms(error_nlms, step_index, n_samples)
    lms_low_rms = late_segment_rms(error_lms, 0, step_index)
    lms_high_rms = late_segment_rms(error_lms, step_index, n_samples)

    nlms_ratio = nlms_low_rms / nlms_high_rms
    lms_ratio = lms_low_rms / lms_high_rms

    assert nlms_ratio < lms_ratio
