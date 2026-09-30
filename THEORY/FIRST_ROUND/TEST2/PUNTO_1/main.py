"""Entry point: TEST2 Punto 1 (AM signal + Hilbert + FIR/IIR filtering).

Saves every figure to `output/`; run with `python main.py`.
"""

from pathlib import Path

import matplotlib.pyplot as plt

from am_hilbert_lab import (
    apply_filter,
    design_fir_bandpass,
    design_fir_lowpass,
    design_iir_bandpass,
    design_iir_lowpass,
    hilbert_envelope,
    load_am_csv,
    single_sided_fft,
)
from am_hilbert_lab.plotting import (
    plot_spectrum,
    plot_stacked_hilbert_filter,
    plot_targeted_filter_attempt,
)

DATA_PATH = Path(__file__).parent.parent / "muestras" / "01_1_modulated_signal_20.0_200.0_40.0.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save(fig, name):
    fig.savefig(OUTPUT_DIR / name, dpi=300)
    plt.close(fig)


# --- Load + verify fs from the data itself (not the filename) ---
t, x, fs = load_am_csv(DATA_PATH)
duration_ms = (t[-1] - t[0]) * 1000
print(f"fs medido = {fs:.1f} Hz, duracion = {duration_ms:.3f} ms, N = {x.size}")

t_ms = t * 1000

# --- (b) Carrier + message frequency, measured from the FFT ---
freqs, mag = single_sided_fft(x, fs, max_freq_hz=fs / 2)
carrier_idx = mag[1:].argmax() + 1  # skip DC bin
carrier_freq = freqs[carrier_idx]

envelope = hilbert_envelope(x)
freqs_env, mag_env = single_sided_fft(envelope - envelope.mean(), fs, max_freq_hz=fs / 2)
message_idx = mag_env.argmax()
message_freq = freqs_env[message_idx]

print(f"Frecuencia portadora (FFT señal cruda) = {carrier_freq:.1f} Hz")
print(f"Frecuencia del mensaje (FFT envolvente Hilbert) = {message_freq:.1f} Hz")

fig = plot_spectrum(freqs, mag, "Punto 1(b): espectro de la señal AM cruda", max_freq_hz=fs / 2)
save(fig, "p1_b_spectrum_raw.png")

fig = plot_spectrum(
    freqs_env, mag_env, "Punto 1(b): espectro de la envolvente de Hilbert (mensaje)", max_freq_hz=10_000
)
save(fig, "p1_b_spectrum_envelope.png")

# --- (c)/(d): Hilbert envelope, then lowpass FIR / IIR to extract the smooth message ---
# Cutoff chosen between the message frequency and the carrier, comfortably
# below f_carrier so the residual carrier ripple in the envelope is removed.
ENVELOPE_CUTOFF_HZ = 5_000

fir_b = design_fir_lowpass(ENVELOPE_CUTOFF_HZ, fs, order=100)
fir_filtered_env = apply_filter(fir_b, [1.0], envelope)
fig = plot_stacked_hilbert_filter(
    t_ms, x, envelope, fir_filtered_env,
    f"Punto 1(c): señal, Hilbert, filtro FIR ({ENVELOPE_CUTOFF_HZ} Hz)",
)
save(fig, "p1_c_hilbert_fir.png")

iir_b, iir_a = design_iir_lowpass(ENVELOPE_CUTOFF_HZ, fs, order=4)
iir_filtered_env = apply_filter(iir_b, iir_a, envelope)
fig = plot_stacked_hilbert_filter(
    t_ms, x, envelope, iir_filtered_env,
    f"Punto 1(d): señal, Hilbert, filtro IIR Butterworth ({ENVELOPE_CUTOFF_HZ} Hz)",
)
save(fig, "p1_d_hilbert_iir.png")

# --- (e): FIR orden 50 + IIR Butterworth orden < 10, dirigidos a f_mensaje sobre la señal cruda ---
BAND_HALF_WIDTH_HZ = 500
low_hz = max(message_freq - BAND_HALF_WIDTH_HZ, 1.0)
high_hz = message_freq + BAND_HALF_WIDTH_HZ

fir_b_e = design_fir_bandpass(low_hz, high_hz, fs, order=50)
fir_out_e = apply_filter(fir_b_e, [1.0], x)

iir_b_e, iir_a_e = design_iir_bandpass(low_hz, high_hz, fs, order=4)
iir_out_e = apply_filter(iir_b_e, iir_a_e, x)

fig = plot_targeted_filter_attempt(
    t_ms, x, fir_out_e, iir_out_e, freqs, mag,
    f"Punto 1(e): FIR orden 50 / IIR orden 4 centrados en f_mensaje ({message_freq:.0f} Hz), sobre la señal cruda",
    max_freq_hz=fs / 2,
)
save(fig, "p1_e_targeted_filter.png")

print(f"Generated {len(list(OUTPUT_DIR.glob('*.png')))} figures in {OUTPUT_DIR}")
