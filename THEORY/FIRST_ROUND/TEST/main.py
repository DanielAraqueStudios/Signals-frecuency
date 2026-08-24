"""TEST CLI - runs items 1-3 and saves figures under report/figuras/.

Usage:
    python main.py            # print stats, save all figures
    python main.py --show     # also open interactive plot windows
"""

from __future__ import annotations

import argparse
import os

import matplotlib

from signal_tools import (
    load_csv_signal,
    segment_signal,
    dominant_frequency as csv_dominant_frequency,
    sample_signal,
    quantize_dac,
    is_aliased,
    load_wav,
)
from signal_tools.audio_fft import compute_fft_spectrum, dominant_frequency as audio_dominant_frequency
from signal_tools.csv_signal import SAMPLE_RATE_HZ, SEGMENT_DURATION_S
from signal_tools.sampling import SIGNAL_FREQUENCY_HZ
from signal_tools.plotting import (
    plot_csv_signal,
    plot_sampling_quantization,
    plot_audio_fft_comparison,
)

HERE = os.path.dirname(os.path.abspath(__file__))
FIGURES_DIR = os.path.join(HERE, "report", "figuras")
SAMPLE_RATES_ITEM2 = [70, 500, 1000]
QUANTIZATION_BITS = 3
DURATION_ITEM2_S = 0.05


def item1(figures_dir: str) -> None:
    print("\n=== Item 1: Muestra01.csv ===")
    signal = load_csv_signal(os.path.join(HERE, "Muestra01.csv"))
    segments = segment_signal(signal, SAMPLE_RATE_HZ, SEGMENT_DURATION_S)
    samples_per_segment = int(SAMPLE_RATE_HZ * SEGMENT_DURATION_S)
    print(f"Total samples: {len(signal)} | fs = {SAMPLE_RATE_HZ} Hz | "
          f"{SEGMENT_DURATION_S}s segments ({samples_per_segment} samples each): {len(segments)}")
    for i, seg in enumerate(segments):
        peak = csv_dominant_frequency(seg, SAMPLE_RATE_HZ)
        print(f"  Segment {i + 1}: dominant frequency = {peak:.2f} Hz")

    fig = plot_csv_signal(signal, segments, SAMPLE_RATE_HZ)
    fig.savefig(os.path.join(figures_dir, "muestra01_analisis.png"), dpi=150, bbox_inches="tight")


def item2(figures_dir: str) -> None:
    print("\n=== Item 2: 100 Hz sine wave, sampling and DAC quantization ===")
    quantized_by_rate = {}
    for fs_m in SAMPLE_RATES_ITEM2:
        t_samples, values = sample_signal(SIGNAL_FREQUENCY_HZ, fs_m, DURATION_ITEM2_S)
        quantized = quantize_dac(values, bits=QUANTIZATION_BITS)
        quantized_by_rate[fs_m] = (t_samples, quantized)
        aliased = is_aliased(SIGNAL_FREQUENCY_HZ, fs_m)
        print(f"  fs = {fs_m} Hz: {len(t_samples)} samples | "
              f"{'ALIASING (fs < 2*f)' if aliased else 'no aliasing (fs >= 2*f)'}")

    fig = plot_sampling_quantization(SIGNAL_FREQUENCY_HZ, DURATION_ITEM2_S, SAMPLE_RATES_ITEM2, quantized_by_rate)
    fig.savefig(os.path.join(figures_dir, "muestreo_cuantizacion.png"), dpi=150, bbox_inches="tight")


def item3(figures_dir: str) -> None:
    print("\n=== Item 3: FFT of violin, drum and cat recordings ===")
    files = {
        "Violin": "violin.wav",
        "Drum": "tambor.wav",
        "Cat": "gato.wav",
    }
    spectra = {}
    for name, filename in files.items():
        path = os.path.join(HERE, "audio_samples", filename)
        sample_rate, signal = load_wav(path)
        spectra[name] = (sample_rate, signal)
        freqs, magnitude = compute_fft_spectrum(signal, sample_rate)
        peak = audio_dominant_frequency(freqs, magnitude)
        print(f"  {name}: fs={sample_rate} Hz, duration={len(signal) / sample_rate:.2f}s, "
              f"dominant frequency = {peak:.2f} Hz")

    fig = plot_audio_fft_comparison(spectra)
    fig.savefig(os.path.join(figures_dir, "audio_fft_comparacion.png"), dpi=150, bbox_inches="tight")


def main() -> None:
    parser = argparse.ArgumentParser(description="TEST: sampling, quantization and FFT")
    parser.add_argument("--show", action="store_true", help="Also display interactive plot windows")
    args = parser.parse_args()

    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(FIGURES_DIR, exist_ok=True)

    item1(FIGURES_DIR)
    item2(FIGURES_DIR)
    item3(FIGURES_DIR)

    print(f"\nFigures saved to: {FIGURES_DIR}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
