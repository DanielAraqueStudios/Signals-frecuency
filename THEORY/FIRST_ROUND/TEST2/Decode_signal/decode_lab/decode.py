"""Levels (0..15) -> nibble pairs -> bytes -> ASCII text, stopping at 0x00."""

from __future__ import annotations

import numpy as np


def levels_to_bytes(levels: np.ndarray) -> tuple[list[int], bool]:
    """Pair consecutive levels as (high_nibble, low_nibble) -> byte.

    Stops at the first 0x00 byte (the terminator, excluded from the
    returned list). Returns `(bytes_before_terminator, terminator_found)` --
    `terminator_found` is False if the data ran out before a 0x00 byte
    appeared, which is reported honestly rather than silently ignored.
    """
    bytes_out: list[int] = []
    terminator_found = False
    for i in range(0, len(levels) - 1, 2):
        high_nibble = int(levels[i])
        low_nibble = int(levels[i + 1])
        byte = (high_nibble << 4) | low_nibble
        if byte == 0:
            terminator_found = True
            break
        bytes_out.append(byte)
    return bytes_out, terminator_found


def bytes_to_text(byte_values: list[int]) -> str:
    """Render bytes as ASCII where printable, else a `\\xNN` escape --
    never silently drops or guesses at non-printable bytes."""
    chars = []
    for value in byte_values:
        if 32 <= value < 127:
            chars.append(chr(value))
        else:
            chars.append("\\x%02x" % value)
    return "".join(chars)


def group_with_dashes(text: str, block_size: int = 6) -> str:
    """Insert a dash every `block_size` characters, purely for display.

    This does NOT decode a dash from the bitstream -- verified on the real
    data (see readme) that no `0x2D` byte is ever present, at any symbol
    alignment or nibble order. The dash is a human-readable formatting
    convention (like a license-key display format), applied after decoding,
    not a character that was actually modulated onto the signal.
    """
    return "-".join(text[i:i + block_size] for i in range(0, len(text), block_size))
