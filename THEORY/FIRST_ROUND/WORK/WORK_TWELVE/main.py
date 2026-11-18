"""Entry point: NLMS system identification, adaptive noise cancellation, and a
direct NLMS-vs-LMS comparison under non-stationary input power.

Saves every figure to `output/`; run with `python main.py`.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from nlms_lab import (
    add_noise,
    lms_filter,
    load_audio,
    nlms_filter,
    sample_times,
    tone_signal,
    varying_power_signal,
)
from nlms_lab.plotting import (
    plot_nlms_vs_lms_varying_power,
    plot_noise_cancellation,
    plot_system_identification,
)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(42)


def save(fig, name):
    fig.savefig(OUTPUT_DIR / name, dpi=300)
    plt.close(fig)


# --- Task 1: system identification -----------------------------------------
# NLMS adapts a filter to match an unknown FIR system driven by white noise.
UNKNOWN_FIR = np.array([0.8, -0.4, 0.25, -0.1, 0.05])
N_SAMPLES_SYSID = 4000
x_sysid = RNG.standard_normal(N_SAMPLES_SYSID)
d_sysid = np.convolve(x_sysid, UNKNOWN_FIR)[: N_SAMPLES_SYSID]

weights_sysid, output_sysid, error_sysid = nlms_filter(
    x_sysid, d_sysid, filter_order=UNKNOWN_FIR.size, mu=0.5
)

fig = plot_system_identification(
    UNKNOWN_FIR, weights_sysid, error_sysid,
    "Tarea 1: identificación de sistema FIR desconocido con NLMS",
)
save(fig, "t1_system_identification.png")

final_weight_error = np.linalg.norm(weights_sysid[-1] - UNKNOWN_FIR)
initial_weight_error = np.linalg.norm(weights_sysid[0] - UNKNOWN_FIR)
print(
    f"[Task 1] weight error: initial={initial_weight_error:.4f} "
    f"final={final_weight_error:.6f}"
)


# --- Task 2: adaptive noise cancellation ------------------------------------
# A 60 Hz reference tone (house convention: WORK_FIVE/WORK_TEN) plus the cat
# audio, both corrupted by additive noise and cleaned up with NLMS.
FS_TONE = 10_000
TONE_DURATION_S = 1.0
t_tone = sample_times(TONE_DURATION_S, FS_TONE)
clean_tone = tone_signal(t_tone, 60)
noisy_tone = add_noise(clean_tone, noise_amplitude=0.5, rng=RNG)

weights_tone, recovered_tone, error_tone = nlms_filter(
    noisy_tone, clean_tone, filter_order=16, mu=0.5
)

fig = plot_noise_cancellation(
    t_tone[:2000], clean_tone[:2000], noisy_tone[:2000], recovered_tone[:2000],
    "Tarea 2: cancelación adaptativa de ruido (NLMS) -- tono 60 Hz", time_unit="s",
)
save(fig, "t2_noise_cancellation_tone.png")

steady_tone = slice(len(recovered_tone) // 2, None)
noisy_error = np.std(noisy_tone[steady_tone] - clean_tone[steady_tone])
recovered_error = np.std(recovered_tone[steady_tone] - clean_tone[steady_tone])
print(f"[Task 2 - tone] std(noisy - clean)={noisy_error:.4f} std(recovered - clean)={recovered_error:.4f}")

cat_audio, cat_fs = load_audio(
    str(Path(__file__).parent / "audio_samples" / "gato" / "gato.ogg")
)
cat_audio = cat_audio[: int(2.0 * cat_fs)]  # first 2 s, keeps the filter fast
t_cat = np.arange(cat_audio.size) / cat_fs
noisy_cat = add_noise(cat_audio, noise_amplitude=0.05, rng=RNG)

weights_cat, recovered_cat, error_cat = nlms_filter(
    noisy_cat, cat_audio, filter_order=32, mu=0.5
)

fig = plot_noise_cancellation(
    t_cat, cat_audio, noisy_cat, recovered_cat,
    "Tarea 2: cancelación adaptativa de ruido (NLMS) -- audio del gato", time_unit="s",
)
save(fig, "t2_noise_cancellation_cat.png")


# --- Task 3: NLMS vs. plain LMS under non-stationary input power -----------
N_SAMPLES_COMPARISON = 6000
LOW_AMPLITUDE, HIGH_AMPLITUDE = 0.05, 2.0
power_step_index = N_SAMPLES_COMPARISON // 2

x_varying = varying_power_signal(N_SAMPLES_COMPARISON, LOW_AMPLITUDE, HIGH_AMPLITUDE, RNG)
d_varying = np.convolve(x_varying, UNKNOWN_FIR)[:N_SAMPLES_COMPARISON]

# A single fixed mu that is safely stable at the high-power segment is
# necessarily slow at the low-power segment (and vice versa) -- picked here
# to be stable throughout, which makes it visibly slow in the low-power half.
FIXED_MU_LMS = 0.05
_, _, error_nlms_varying = nlms_filter(x_varying, d_varying, filter_order=UNKNOWN_FIR.size, mu=0.5)
_, _, error_lms_varying = lms_filter(x_varying, d_varying, filter_order=UNKNOWN_FIR.size, mu=FIXED_MU_LMS)

fig = plot_nlms_vs_lms_varying_power(
    x_varying, error_nlms_varying, error_lms_varying, power_step_index,
    "Tarea 3: NLMS vs. LMS con potencia de entrada no estacionaria",
)
save(fig, "t3_nlms_vs_lms_varying_power.png")

# Per-segment error magnitude: NLMS should stay comparably small in both
# halves, while fixed-mu LMS is disproportionately worse in the low-power
# half (too slow relative to its own signal scale) given a mu chosen to
# stay stable at the high-power half.
low_half = slice(0, power_step_index)
high_half = slice(power_step_index, None)
nlms_low_rms = np.sqrt(np.mean(error_nlms_varying[low_half] ** 2))
lms_low_rms = np.sqrt(np.mean(error_lms_varying[low_half] ** 2))
print(f"[Task 3] low-power RMS error: NLMS={nlms_low_rms:.5f} LMS={lms_low_rms:.5f}")

print(f"Generated {len(list(OUTPUT_DIR.glob('*.png')))} figures in {OUTPUT_DIR}")
