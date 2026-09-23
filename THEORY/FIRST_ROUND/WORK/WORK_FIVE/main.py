from pathlib import Path

import matplotlib.pyplot as plt

from am_lab import modulated_signal, sample_times, single_sided_fft, tone_signal

# Set up figure
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# --- Case 1: fs = 10^5 Hz (Strict user specification) ---
fs1 = 10**5
t1 = sample_times(0.05, fs1)
x1_fs1 = modulated_signal(t1, 60, 10**3)
x2_fs1 = tone_signal(t1, 60)

# --- Case 2: fs = 10^6 Hz (Correct Nyquist sampling to visualize AM signal) ---
fs2 = 10**6
t2 = sample_times(0.05, fs2)
x1_fs2 = modulated_signal(t2, 60, 10**5)
freqs2, X1_fft_fs2 = single_sided_fft(x1_fs2, fs2, max_freq_hz=150000)

# Plotting:
# Top Left: Signal 2 in time (60 Hz)
axes[0, 0].plot(t1 * 1000, x2_fs1, color='tab:orange', linewidth=1.2)
axes[0, 0].set_title(r'Señal 2 en el Tiempo: $\sin(2\pi \cdot 60 t)$')
axes[0, 0].set_xlabel('Tiempo (ms)')
axes[0, 0].set_ylabel('Amplitud')
axes[0, 0].grid(True, linestyle=':')

# Top Right: FFT of Signal 2
freqs_60, X2_fft = single_sided_fft(x2_fs1, fs1, max_freq_hz=200)
axes[0, 1].stem(freqs_60, X2_fft, linefmt='m-', markerfmt='mo', basefmt='r-')
axes[0, 1].set_title(r'FFT Señal 2 ($\sin(2\pi \cdot 60 t)$) — Pico en 60 Hz')
axes[0, 1].set_xlabel('Frecuencia (Hz)')
axes[0, 1].set_ylabel('Magnitud')
axes[0, 1].grid(True, linestyle=':')

# Bottom Left: Signal 1 at fs = 10^5 Hz (Aliasing/Zero crossings)
axes[1, 0].plot(t1 * 1000, x1_fs1, color='tab:red', linewidth=1)
axes[1, 0].set_title(r'Señal 1 con $f_s = 10^5$ Hz (portadora 1 kHz, no aliasing)')
axes[1, 0].set_xlabel('Tiempo (ms)')
axes[1, 0].set_ylabel('Amplitud')
axes[1, 0].grid(True, linestyle=':')

# Bottom Right: Signal 1 FFT with proper sampling fs = 10^6 Hz for comparison
axes[1, 1].stem(freqs2/1000, X1_fft_fs2, linefmt='b-', markerfmt='bo', basefmt='r-')
axes[1, 1].set_title(r'FFT Señal 1 con $f_s = 10^6$ Hz (Portadora 100 kHz y Bandas Laterales)')
axes[1, 1].set_xlabel('Frecuencia (kHz)')
axes[1, 1].set_ylabel('Magnitud')
axes[1, 1].grid(True, linestyle=':')

plt.tight_layout()

output_dir = Path(__file__).parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)
plt.savefig(output_dir / "analisis_senales_fft.png", dpi=300)
plt.show()
