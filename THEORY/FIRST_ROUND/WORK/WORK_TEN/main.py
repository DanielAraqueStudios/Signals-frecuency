"""Entry point: tasks 6, 6.1, 6.2, 6.3, 6.4 (FIR/IIR filtering + Hilbert envelope).

Saves every figure to `output/`; run with `python main.py`.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from fir_iir_lab import (
    am_modulate,
    apply_filter,
    design_fir_lowpass,
    design_iir_lowpass,
    hilbert_envelope,
    load_audio,
    remove_negative_frequencies,
    sample_times,
    single_sided_fft,
    tone_signal,
)
from fir_iir_lab.plotting import (
    plot_filter_comparison,
    plot_hilbert_envelope_filtered,
    plot_negative_freq_removal,
    plot_order_sweep,
)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save(fig, name):
    fig.savefig(OUTPUT_DIR / name, dpi=300)
    plt.close(fig)


# --- Task 6: 60 Hz "long signal", negative-frequency removal, FIR/IIR @ 300 Hz ---
# fs matches WORK_FIVE's 60 Hz reference (fs1 = 10**5); duration extended to
# 1.0 s (vs. WORK_FIVE's 0.05 s default) so this counts as the "long signal"
# the assignment asks for and gives a well-resolved FFT (1 Hz bin spacing).
FS_60HZ = 10**5
LONG_DURATION_S = 1.0
t_long = sample_times(LONG_DURATION_S, FS_60HZ)
signal_60hz = tone_signal(t_long, 60)

analytic_60hz = remove_negative_frequencies(signal_60hz)
fig = plot_negative_freq_removal(
    t_long[:2000] * 1000, signal_60hz[:2000], analytic_60hz[:2000],
    "Tarea 6: señal 60 Hz -- eliminación de frecuencia negativa (FFT)",
)
save(fig, "t6_negative_freq_removal.png")

fir_b_300 = design_fir_lowpass(300, FS_60HZ, order=100)
fir_out_300 = apply_filter(fir_b_300, [1.0], signal_60hz)
iir_b_300, iir_a_300 = design_iir_lowpass(300, FS_60HZ, order=4)
iir_out_300 = apply_filter(iir_b_300, iir_a_300, signal_60hz)

freqs_60, fft_orig_60 = single_sided_fft(signal_60hz, FS_60HZ, max_freq_hz=1000)
_, fft_fir_60 = single_sided_fft(fir_out_300, FS_60HZ, max_freq_hz=1000)
_, fft_iir_60 = single_sided_fft(iir_out_300, FS_60HZ, max_freq_hz=1000)

fig = plot_filter_comparison(
    t_long[:5000] * 1000, signal_60hz[:5000], fir_out_300[:5000], iir_out_300[:5000],
    freqs_60, fft_orig_60, fft_fir_60, fft_iir_60,
    "Tarea 6: filtro 300 Hz (FIR vs IIR) sobre señal 60 Hz", time_unit="ms",
)
save(fig, "t6_fir_iir_300hz.png")


# --- Task 6.1: AM-modulated cat audio, negative-freq removal, FIR/IIR @ 10 kHz ---
# Self-contained AM modulation (per teammate brief): the cat audio is
# amplitude-modulated locally here using the same `message * carrier` scheme
# as WORK_FIVE/am_lab.modulated_signal, standing in for "the modulated gato
# audio from Tarea 5" without depending on WORK_NINE's concurrent work.
cat_audio, cat_fs = load_audio(str(Path(__file__).parent / "audio_samples" / "gato" / "gato.ogg"))
cat_audio = cat_audio[: int(2.0 * cat_fs)]  # first 2 s, keeps FFT/filters fast
t_cat = np.arange(cat_audio.size) / cat_fs
CARRIER_FREQ_CAT = 20_000  # Hz; well above the audio band, below cat_fs/2
modulated_cat = am_modulate(cat_audio, t_cat, CARRIER_FREQ_CAT)

analytic_cat = remove_negative_frequencies(modulated_cat)
fig = plot_negative_freq_removal(
    t_cat[:2000] * 1000, modulated_cat[:2000], analytic_cat[:2000],
    "Tarea 6.1: gato modulado (AM) -- eliminación de frecuencia negativa (FFT)",
)
save(fig, "t6_1_negative_freq_removal_cat.png")

fir_b_10k = design_fir_lowpass(10_000, cat_fs, order=200)
fir_out_cat = apply_filter(fir_b_10k, [1.0], modulated_cat)
iir_b_10k, iir_a_10k = design_iir_lowpass(10_000, cat_fs, order=4)
iir_out_cat = apply_filter(iir_b_10k, iir_a_10k, modulated_cat)

freqs_cat, fft_orig_cat = single_sided_fft(modulated_cat, cat_fs, max_freq_hz=cat_fs / 2)
_, fft_fir_cat = single_sided_fft(fir_out_cat, cat_fs, max_freq_hz=cat_fs / 2)
_, fft_iir_cat = single_sided_fft(iir_out_cat, cat_fs, max_freq_hz=cat_fs / 2)

fig = plot_filter_comparison(
    t_cat[:5000] * 1000, modulated_cat[:5000], fir_out_cat[:5000], iir_out_cat[:5000],
    freqs_cat, fft_orig_cat, fft_fir_cat, fft_iir_cat,
    "Tarea 6.1: filtro 10 kHz (FIR vs IIR) sobre gato modulado (AM)", time_unit="ms",
)
save(fig, "t6_1_fir_iir_10khz_cat.png")


# --- Task 6.2: Hilbert transform of the long 60 Hz signal, then 300 Hz filter on its magnitude ---
envelope_60hz = hilbert_envelope(signal_60hz)
filtered_envelope_60hz = apply_filter(fir_b_300, [1.0], envelope_60hz)
fig = plot_hilbert_envelope_filtered(
    t_long[:5000], envelope_60hz[:5000], filtered_envelope_60hz[:5000],
    "Tarea 6.2: envolvente de Hilbert (señal 60 Hz) filtrada a 300 Hz",
)
save(fig, "t6_2_hilbert_envelope_60hz.png")


# --- Task 6.3: same as 6.2, on the modulated cat audio ---
envelope_cat = hilbert_envelope(modulated_cat)
filtered_envelope_cat = apply_filter(fir_b_10k, [1.0], envelope_cat)
fig = plot_hilbert_envelope_filtered(
    t_cat, envelope_cat, filtered_envelope_cat,
    "Tarea 6.3: envolvente de Hilbert (gato modulado) filtrada a 10 kHz", time_unit="s",
)
save(fig, "t6_3_hilbert_envelope_cat.png")


# --- Task 6.4: order sweep of the 300 Hz FIR filter, orders including >= 10 ---
ORDERS = [2, 10, 20, 50, 100]
outputs_by_order = {}
ffts_by_order = {}
for order in ORDERS:
    b = design_fir_lowpass(300, FS_60HZ, order=order)
    y = apply_filter(b, [1.0], signal_60hz)
    outputs_by_order[order] = y[:5000]
    _, mag = single_sided_fft(y, FS_60HZ, max_freq_hz=1000)
    ffts_by_order[order] = mag

fig = plot_order_sweep(
    t_long[:5000] * 1000, signal_60hz[:5000], outputs_by_order,
    freqs_60, ffts_by_order,
    "Tarea 6.4: filtro FIR 300 Hz -- barrido de orden (incl. orden >= 10)",
)
save(fig, "t6_4_order_sweep.png")

print(f"Generated {len(list(OUTPUT_DIR.glob('*.png')))} figures in {OUTPUT_DIR}")
