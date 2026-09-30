"""Bits -> bytes -> ASCII, searching alignment/bit-order (task 2c)."""

from __future__ import annotations

import numpy as np


def _bits_to_text(bits: np.ndarray, msb_first: bool) -> str:
    chars = []
    for i in range(0, len(bits) - 7, 8):
        byte_bits = bits[i : i + 8]
        if not msb_first:
            byte_bits = byte_bits[::-1]
        value = 0
        for bit in byte_bits:
            value = (value << 1) | int(bit)
        chars.append(chr(value))
    return "".join(chars)


def _printable_score(text: str) -> int:
    return sum(1 for c in text if c.isprintable() and (c == " " or not c.isspace()))


def best_ascii_decoding(bits: np.ndarray) -> dict:
    """Try all 8 bit-offsets x 2 bit-orders, return the best-scoring decode.

    Returns a dict with keys: text, offset, msb_first, score, bits_used.
    """
    best = None
    for offset in range(8):
        shifted = bits[offset:]
        for msb_first in (True, False):
            text = _bits_to_text(shifted, msb_first)
            score = _printable_score(text)
            candidate = {
                "text": text,
                "offset": offset,
                "msb_first": msb_first,
                "score": score,
                "n_bytes": len(text),
            }
            if best is None or score > best["score"]:
                best = candidate
    return best
