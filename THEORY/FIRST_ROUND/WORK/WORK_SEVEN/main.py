from pathlib import Path

import matplotlib.pyplot as plt

from avg_filter_lab import (
    load_audio,
    moving_average_by_cutoff,
    sample_times,
    segment,
    sine_am,
    sine_tone,
    square_am,
    square_tone,
)
from avg_filter_lab.plotting import plot_filter_comparison

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

figures = []


def run_case(t, x, sample_rate, cutoff_hz, title, filename, max_freq_hz=None):
    filtered, window = moving_average_by_cutoff(x, cutoff_hz, sample_rate)
    fig = plot_filter_comparison(t, x, filtered, sample_rate, cutoff_hz, window, title, max_freq_hz)
    fig.savefig(OUTPUT_DIR / filename, dpi=300)
    figures.append(fig)


# --- C.1: moving-average filter at 40Hz and 100Hz for A (sine) and B (AM) ---
fs1 = 10**5
t1 = sample_times(0.05, fs1)
signal_a_sine = sine_tone(t1, 60)
signal_b_sine = sine_am(t1, 60, 10**3)

for cutoff in (40, 100):
    run_case(
        t1, signal_a_sine, fs1, cutoff,
        f"C.1 - Señal A (seno 60Hz) filtrada a {cutoff}Hz",
        f"c1_a_seno_{cutoff}hz.png",
        max_freq_hz=200,
    )
    run_case(
        t1, signal_b_sine, fs1, cutoff,
        f"C.1 - Señal B (AM) filtrada a {cutoff}Hz",
        f"c1_b_am_{cutoff}hz.png",
        max_freq_hz=1200,
    )

# --- C.2: moving-average filter at 40Hz, 70Hz, 120Hz for square A and B ---
signal_a_square = square_tone(t1, 60)
signal_b_square = square_am(t1, 60, 10**3)

for cutoff in (40, 70, 120):
    run_case(
        t1, signal_a_square, fs1, cutoff,
        f"C.2 - Señal A (cuadrada 60Hz) filtrada a {cutoff}Hz",
        f"c2_a_cuadrada_{cutoff}hz.png",
        max_freq_hz=600,
    )
    run_case(
        t1, signal_b_square, fs1, cutoff,
        f"C.2 - Señal B (cuadrada AM) filtrada a {cutoff}Hz",
        f"c2_b_cuadrada_am_{cutoff}hz.png",
        max_freq_hz=3000,
    )

# --- C.3: moving-average filter at 40Hz and 100Hz for cat audio ---
audio_path = Path(__file__).parent / "audio_samples" / "gato" / "gato.ogg"
cat_signal, cat_fs = load_audio(str(audio_path))
cat_segment = segment(cat_signal, cat_fs, duration_s=0.05, start_s=0.5)
t_cat = sample_times(0.05, cat_fs)[: cat_segment.size]

for cutoff in (40, 100):
    run_case(
        t_cat, cat_segment, cat_fs, cutoff,
        f"C.3 - Audio de gato filtrado a {cutoff}Hz",
        f"c3_gato_{cutoff}hz.png",
        max_freq_hz=2000,
    )

plt.show()
