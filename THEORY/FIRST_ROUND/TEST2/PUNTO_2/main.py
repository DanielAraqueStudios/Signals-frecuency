"""Punto 2: decode the ASCII message hidden in an OOK-modulated bit signal.

Steps (a)(b)(c) per the assignment; see readme.md for the write-up.
"""

from __future__ import annotations

import os

from bitstream_lab.bits import bits_from_envelope, smooth_envelope, square_wave_from_bits
from bitstream_lab.data import load_signal
from bitstream_lab.decode import best_ascii_decoding
from bitstream_lab.filters import apply_filter, design_fir_lowpass, design_iir_lowpass
from bitstream_lab.hilbert_tools import hilbert_envelope
from bitstream_lab.plotting import plot_filtered_at_bit_rate, plot_hilbert_and_bits, plot_spectrum
from bitstream_lab.spectrum import single_sided_fft

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(
    HERE, "..", "muestras", "01_2_modulated_signal_10.0_100.0_1.0.csv"
)
OUTPUT_DIR = os.path.join(HERE, "output")

CARRIER_HZ = 10_000.0
BIT_PERIOD_S = 1e-3


def main() -> None:
    t, raw, fs = load_signal(CSV_PATH)
    print(f"Loaded {len(raw)} samples, fs = {fs:.1f} Hz, duration = {t[-1]:.5f} s")

    bit_rate_hz = 1.0 / BIT_PERIOD_S

    # (a) FIR order 50 / IIR Butterworth order < 10 at the bit frequency
    fir_taps = design_fir_lowpass(bit_rate_hz, fs, order=50)
    fir_out = apply_filter(fir_taps, [1.0], raw)
    iir_b, iir_a = design_iir_lowpass(bit_rate_hz, fs, order=6)
    iir_out = apply_filter(iir_b, iir_a, raw)
    plot_filtered_at_bit_rate(t, raw, fir_out, iir_out, os.path.join(OUTPUT_DIR, "t2a_filtered_bit_rate.png"))

    freqs, magnitude = single_sided_fft(raw, fs)
    plot_spectrum(freqs, magnitude, bit_rate_hz, CARRIER_HZ, os.path.join(OUTPUT_DIR, "t2a_spectrum.png"))
    print(
        "(a) Filtering the raw OOK signal directly at 1/T = "
        f"{bit_rate_hz:.0f} Hz does not reveal the square bit pattern: "
        "the signal's energy sits around the carrier "
        f"({CARRIER_HZ:.0f} Hz) with sidebands, not at the bit rate itself "
        "-- see t2a_spectrum.png for the real FFT evidence."
    )

    # (b) Hilbert envelope + reconstructed square wave
    envelope = hilbert_envelope(raw)
    smoothed = smooth_envelope(envelope, fs, BIT_PERIOD_S)
    bits, per_bit_avg = bits_from_envelope(smoothed, fs, BIT_PERIOD_S)
    square_wave = square_wave_from_bits(bits, fs, BIT_PERIOD_S)
    plot_hilbert_and_bits(t, raw, envelope, square_wave, os.path.join(OUTPUT_DIR, "t2b_hilbert_bits.png"))
    print(f"(b) Recovered {len(bits)} bits: {''.join(str(b) for b in bits)}")

    # (c) Bits -> ASCII
    result = best_ascii_decoding(bits)
    print(
        f"(c) Best decode: offset={result['offset']} msb_first={result['msb_first']} "
        f"score={result['score']}/{result['n_bytes']}"
    )
    print(f"(c) DECODED MESSAGE: {result['text']!r}")


if __name__ == "__main__":
    main()
