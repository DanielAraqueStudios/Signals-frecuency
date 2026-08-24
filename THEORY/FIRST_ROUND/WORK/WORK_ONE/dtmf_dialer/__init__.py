"""DTMF dial-tone synthesis, WAV export, and playback."""

from .dtmf import (
    DTMF_FREQUENCIES,
    generate_dtmf_sequence,
    generate_silence,
    generate_tone,
    play_wav,
    save_wav,
)

__all__ = [
    "DTMF_FREQUENCIES",
    "generate_tone",
    "generate_silence",
    "generate_dtmf_sequence",
    "save_wav",
    "play_wav",
]
