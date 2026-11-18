"""Entry point: tasks 1 (system identification), 2 (adaptive noise
cancellation), 3 (convergence vs. step size mu).

Saves every figure to `output/`; run with `python main.py`.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lms_lab import (
    apply_unknown_system,
    load_audio,
    run_lms,
    sample_times,
    tone_signal,
    unknown_fir_coefficients,
    white_noise,
)
from lms_lab.plotting import (
    plot_identification_error,
    plot_mu_sweep,
    plot_noise_cancellation,
    plot_weight_convergence,
)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(seed=42)


def save(fig, name):
    fig.savefig(OUTPUT_DIR / name, dpi=300)
    plt.close(fig)


# --- Task 1: system identification -----------------------------------------
# Feed LMS a known input and the output of an "unknown" FIR filter; the
# adapted weights should converge toward the unknown filter's true taps.
FS_ID = 2_000
DURATION_ID = 2.0
N_TAPS_ID = 5
MU_ID = 0.02

t_id = sample_times(DURATION_ID, FS_ID)
x_id = white_noise(len(t_id), power=1.0, rng=RNG)
h_true = unknown_fir_coefficients()
d_id = apply_unknown_system(x_id, h_true)

y_id, e_id, w_history = run_lms(x_id, d_id, n_taps=N_TAPS_ID, mu=MU_ID)

fig = plot_weight_convergence(
    w_history, h_true,
    "Tarea 1: identificación de sistema -- convergencia de pesos LMS hacia los coeficientes reales",
)
save(fig, "t1_weight_convergence.png")

fig = plot_identification_error(e_id, "Tarea 1: error de identificación e[n]")
save(fig, "t1_identification_error.png")

final_w = w_history[-1]
print(f"Task 1: true h = {h_true}")
print(f"Task 1: final w = {np.round(final_w, 4)}")
print(f"Task 1: ||w_final - h_true|| = {np.linalg.norm(final_w - h_true):.4f}")


# --- Task 2: adaptive noise cancellation ------------------------------------
# Clean reference tone (house convention: 60 Hz, per WORK_FIVE/WORK_TEN),
# corrupted by noise correlated with a second "reference noise" input (as in
# a real adaptive-noise-canceller setup); LMS adapts a filter on the noise
# reference to estimate and subtract the noise from the corrupted signal.
FS_ANC = 5_000
DURATION_ANC = 1.0
N_TAPS_ANC = 8
MU_ANC = 0.01

t_anc = sample_times(DURATION_ANC, FS_ANC)
clean_tone = tone_signal(t_anc, 60, amplitude=1.0)

noise_source = white_noise(len(t_anc), power=1.0, rng=RNG)
noise_filter_true = np.array([0.5, 0.3, -0.2, 0.1])
correlated_noise = apply_unknown_system(noise_source, noise_filter_true)
noisy_tone = clean_tone + correlated_noise

# `noise_source` plays the role of the ANC reference microphone; LMS learns
# the path from it to the noise actually added to `noisy_tone`, using the
# corrupted signal itself as the desired output, then the *error* (desired
# minus the LMS-estimated noise) is the cleaned signal.
_, e_anc, _ = run_lms(noise_source, noisy_tone, n_taps=N_TAPS_ANC, mu=MU_ANC)
recovered_tone = e_anc

fig = plot_noise_cancellation(
    t_anc, clean_tone, noisy_tone, recovered_tone,
    "Tarea 2: cancelación adaptativa de ruido (tono de 60 Hz)",
)
save(fig, "t2_noise_cancellation_tone.png")

residual_before = np.std(noisy_tone[len(t_anc) // 2 :] - clean_tone[len(t_anc) // 2 :])
residual_after = np.std(recovered_tone[len(t_anc) // 2 :] - clean_tone[len(t_anc) // 2 :])
print(f"Task 2 (tone): residual std before = {residual_before:.4f}, after = {residual_after:.4f}")


# --- Task 2b: adaptive noise cancellation on the cat audio ------------------
cat_audio, cat_fs = load_audio(str(Path(__file__).parent / "audio_samples" / "gato" / "gato.ogg"))
cat_audio = cat_audio[: int(2.0 * cat_fs)]  # first 2 s, keeps LMS fast
cat_audio = cat_audio / (np.max(np.abs(cat_audio)) + 1e-12)
t_cat = np.arange(cat_audio.size) / cat_fs

cat_noise_source = white_noise(len(t_cat), power=1.0, rng=RNG)
cat_noise_filter_true = np.array([0.6, -0.25, 0.15])
cat_correlated_noise = 0.5 * apply_unknown_system(cat_noise_source, cat_noise_filter_true)
noisy_cat = cat_audio + cat_correlated_noise

_, e_cat, _ = run_lms(cat_noise_source, noisy_cat, n_taps=8, mu=0.01)
recovered_cat = e_cat

fig = plot_noise_cancellation(
    t_cat, cat_audio, noisy_cat, recovered_cat,
    "Tarea 2b: cancelación adaptativa de ruido (audio de gato)", time_unit="s",
)
save(fig, "t2b_noise_cancellation_cat.png")


# --- Task 3: convergence behavior vs. step size mu --------------------------
# Re-run the system-identification problem at several values of mu and track
# the learning curve (moving-average MSE) plus the final residual error.
MUS = [0.001, 0.01, 0.05, 0.1, 0.5]
MOVING_AVG_WINDOW = 50

mse_curves = {}
final_mse = {}
for mu in MUS:
    _, e_mu, w_hist_mu = run_lms(x_id, d_id, n_taps=N_TAPS_ID, mu=mu)
    sq_err = e_mu**2
    kernel = np.ones(MOVING_AVG_WINDOW) / MOVING_AVG_WINDOW
    mse_curve = np.convolve(sq_err, kernel, mode="same")
    mse_curves[mu] = mse_curve

    tail = sq_err[-200:]
    final_mse[mu] = np.mean(tail) if np.all(np.isfinite(tail)) else np.inf
    if not np.all(np.isfinite(w_hist_mu[-1])):
        final_mse[mu] = np.inf

fig = plot_mu_sweep(mse_curves, final_mse, "Tarea 3: convergencia LMS vs. paso de adaptación (mu)")
save(fig, "t3_mu_sweep.png")

print("Task 3: final MSE by mu:")
for mu in MUS:
    print(f"  mu = {mu:<6g} final MSE = {final_mse[mu]:.6g}")

print(f"Generated {len(list(OUTPUT_DIR.glob('*.png')))} figures in {OUTPUT_DIR}")
