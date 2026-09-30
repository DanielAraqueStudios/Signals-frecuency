"""Unit tests for decode.py helpers."""

from __future__ import annotations

import numpy as np

from bitstream_lab.decode import _bits_to_text, best_ascii_decoding


def test_bits_to_text_msb_first():
    text = "Hola mundo DSP"
    bits = []
    for ch in text:
        for shift in range(7, -1, -1):
            bits.append((ord(ch) >> shift) & 1)
    assert _bits_to_text(np.array(bits), msb_first=True) == text


def test_bits_to_text_lsb_first():
    text = "Signal test"
    bits = []
    for ch in text:
        for shift in range(8):
            bits.append((ord(ch) >> shift) & 1)
    assert _bits_to_text(np.array(bits), msb_first=False) == text


def test_best_ascii_decoding_finds_correct_offset_with_long_text():
    text = "Hola mundo, esto es una prueba de decodificacion ASCII larga"
    bits = []
    for ch in text:
        for shift in range(7, -1, -1):
            bits.append((ord(ch) >> shift) & 1)
    padded = [0, 1, 0] + bits  # misaligned by 3 junk bits
    result = best_ascii_decoding(np.array(padded))
    assert result["text"] == text
    assert result["offset"] == 3
    assert result["msb_first"] is True
