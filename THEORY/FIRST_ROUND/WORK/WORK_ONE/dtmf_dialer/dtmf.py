"""DTMF (dual-tone multi-frequency) dial-tone synthesis, WAV export, and playback.

Encodes phone-keypad digits as the standard ITU-T Q.23 tone pairs (one
low-group frequency + one high-group frequency per digit), synthesizes the
audio with NumPy, and writes/plays it as a mono 16-bit PCM WAV file.
"""

from __future__ import annotations

import winsound

import numpy as np
from scipy.io import wavfile

# Standard DTMF frequency pairs (Hz): (low_group_freq, high_group_freq).
DTMF_FREQUENCIES: dict[str, tuple[int, int]] = {
    "1": (697, 1209), "2": (697, 1336), "3": (697, 1477),
    "4": (770, 1209), "5": (770, 1336), "6": (770, 1477),
    "7": (852, 1209), "8": (852, 1336), "9": (852, 1477),
    "0": (941, 1336),
}


def generate_tone(
    low_freq_hz: float, high_freq_hz: float, duration_s: float, sample_rate: int
) -> np.ndarray:
    """Synthesize one DTMF tone as the sum of its two component sine waves.

    Args:
        low_freq_hz: Low-group frequency of the key (e.g. 697-941 Hz).
        high_freq_hz: High-group frequency of the key (e.g. 1209-1477 Hz).
        duration_s: Tone length in seconds.
        sample_rate: Samples per second (Hz).

    Returns:
        int16 PCM samples for the mixed tone.
    """
    t = np.arange(int(sample_rate * duration_s)) / sample_rate
    # Average (not sum) the two sines so the mix stays within [-1, 1] before scaling.
    mixed = 0.5 * (np.sin(2 * np.pi * low_freq_hz * t) + np.sin(2 * np.pi * high_freq_hz * t))
    return (mixed * 16000).astype(np.int16)


def generate_silence(duration_s: float, sample_rate: int) -> np.ndarray:
    """Generate a block of silence used to separate consecutive tones.

    Args:
        duration_s: Silence length in seconds.
        sample_rate: Samples per second (Hz).

    Returns:
        int16 zero-valued PCM samples.
    """
    return np.zeros(int(sample_rate * duration_s), dtype=np.int16)


def generate_dtmf_sequence(
    digits: str,
    tone_duration_s: float = 0.5,
    pause_duration_s: float = 0.05,
    sample_rate: int = 44100,
) -> np.ndarray:
    """Synthesize a full DTMF dial sequence for a string of digits.

    Args:
        digits: Digits to encode (0-9). Characters outside `DTMF_FREQUENCIES`
            are skipped.
        tone_duration_s: Length of each tone in seconds.
        pause_duration_s: Silence inserted between tones, in seconds.
        sample_rate: Samples per second (Hz).

    Returns:
        Concatenated int16 PCM samples for the whole sequence.
    """
    silence = generate_silence(pause_duration_s, sample_rate)
    blocks = [
        block
        for digit in digits
        if digit in DTMF_FREQUENCIES
        for block in (generate_tone(*DTMF_FREQUENCIES[digit], tone_duration_s, sample_rate), silence)
    ]
    return np.concatenate(blocks) if blocks else np.array([], dtype=np.int16)


def save_wav(samples: np.ndarray, path: str, sample_rate: int = 44100) -> None:
    """Write mono int16 PCM samples to a `.wav` file.

    Args:
        samples: int16 PCM samples to write.
        path: Destination file path.
        sample_rate: Samples per second (Hz).
    """
    wavfile.write(path, sample_rate, samples)


def play_wav(path: str) -> None:
    """Play a `.wav` file synchronously through Windows audio.

    Args:
        path: Path to the `.wav` file to play.
    """
    winsound.PlaySound(path, winsound.SND_FILENAME)
