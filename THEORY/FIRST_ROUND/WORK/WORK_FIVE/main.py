from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# Set up figure
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# --- Case 1: fs = 10^5 Hz (Strict user specification) ---
fs1 = 10**5
t1 = np.linspace(0, 0.05, int(fs1 * 0.05), endpoint=False)
x1_fs1 = (2 + np.sin(2 * np.pi * 60 * t1)) * np.sin(2 * np.pi * 10**3 * t1)
x2_fs1 = np.sin(2 * np.pi * 60 * t1)

N1 = len(t1)
freqs1 = np.fft.fftfreq(N1, 1/fs1)
pos1 = freqs1 >= 0
X1_fft_fs1 = np.abs(np.fft.fft(x1_fs1))[pos1] / (N1/2)

# --- Case 2: fs = 10^6 Hz (Correct Nyquist sampling to visualize AM signal) ---
fs2 = 10**6
t2 = np.linspace(0, 0.05, int(fs2 * 0.05), endpoint=False)
x1_fs2 = (2 + np.sin(2 * np.pi * 60 * t2)) * np.sin(2 * np.pi * 10**5 * t2)

N2 = len(t2)
freqs2 = np.fft.fftfreq(N2, 1/fs2)
pos2 = (freqs2 >= 0) & (freqs2 <= 150000)
X1_fft_fs2 = np.abs(np.fft.fft(x1_fs2))[pos2] / (N2/2)

# Plotting:
# Top Left: Signal 2 in time (60 Hz)
axes[0, 0].plot(t1 * 1000, x2_fs1, color='tab:orange', linewidth=1.2)
axes[0, 0].set_title(r'Señal 2 en el Tiempo: $\sin(2\pi \cdot 60 t)$')
axes[0, 0].set_xlabel('Tiempo (ms)')
axes[0, 0].set_ylabel('Amplitud')
axes[0, 0].grid(True, linestyle=':')

# Top Right: FFT of Signal 2
N_60 = len(t1)
freqs_60 = np.fft.fftfreq(N_60, 1/fs1)
pos_60 = (freqs_60 >= 0) & (freqs_60 <= 200)
X2_fft = np.abs(np.fft.fft(x2_fs1))[pos_60] / (N_60/2)
axes[0, 1].stem(freqs_60[pos_60], X2_fft, linefmt='m-', markerfmt='mo', basefmt='r-')
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
axes[1, 1].stem(freqs2[pos2]/1000, X1_fft_fs2, linefmt='b-', markerfmt='bo', basefmt='r-')
axes[1, 1].set_title(r'FFT Señal 1 con $f_s = 10^6$ Hz (Portadora 100 kHz y Bandas Laterales)')
axes[1, 1].set_xlabel('Frecuencia (kHz)')
axes[1, 1].set_ylabel('Magnitud')
axes[1, 1].grid(True, linestyle=':')

plt.tight_layout()

output_dir = Path(__file__).parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)
plt.savefig(output_dir / "analisis_senales_fft.png", dpi=300)
plt.show()