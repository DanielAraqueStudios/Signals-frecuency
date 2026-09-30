"""Synthetic OOK signal with a known ASCII string: verify full decode pipeline."""

from __future__ import annotations

import numpy as np

from bitstream_lab.bits import bits_from_envelope, smooth_envelope, square_wave_from_bits
from bitstream_lab.decode import best_ascii_decoding
from bitstream_lab.hilbert_tools import hilbert_envelope

KNOWN_TEXT = "Hi DSP!"
FS = 100_000.0
BIT_PERIOD_S = 1e-3
CARRIER_HZ = 10_000.0


def _text_to_bits(text: str) -> np.ndarray:
    bits = []
    for ch in text:
        value = ord(ch)
        for shift in range(7, -1, -1):
            bits.append((value >> shift) & 1)
    return np.array(bits)


def _make_ook_signal(bits: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    samples_per_bit = int(round(BIT_PERIOD_S * FS))
    n = len(bits) * samples_per_bit
    t = np.arange(n) / FS
    carrier = np.sin(2 * np.pi * CARRIER_HZ * t)
    envelope = np.repeat(bits, samples_per_bit).astype(float)
    signal = envelope * carrier
    return t, signal


def test_known_string_round_trip():
    known_bits = _text_to_bits(KNOWN_TEXT)
    t, signal = _make_ook_signal(known_bits)

    envelope = hilbert_envelope(signal)
    smoothed = smooth_envelope(envelope, FS, BIT_PERIOD_S)
    recovered_bits, _ = bits_from_envelope(smoothed, FS, BIT_PERIOD_S)

    assert len(recovered_bits) == len(known_bits)
    assert np.array_equal(recovered_bits, known_bits)

    result = best_ascii_decoding(recovered_bits)
    assert result["text"] == KNOWN_TEXT
    assert result["offset"] == 0
    assert result["msb_first"] is True


def test_square_wave_matches_bits():
    bits = np.array([0, 1, 1, 0, 1])
    wave = square_wave_from_bits(bits, FS, BIT_PERIOD_S)
    samples_per_bit = int(round(BIT_PERIOD_S * FS))
    assert len(wave) == len(bits) * samples_per_bit
    assert np.all(wave[:samples_per_bit] == 0)
    assert np.all(wave[samples_per_bit : 2 * samples_per_bit] == 1)
