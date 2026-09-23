"""AM modulation of a message signal at a target sample rate (Tarea 5).

Pure, dependency-light functions (numpy only): given samples + sample rate,
produce an amplitude-modulated signal at a requested target sample rate.
Resampling uses `librosa.resample` (lazy import), kept out of the pure
functions below so they stay testable without it installed.
"""

from __future__ import annotations

import numpy as np

# Carrier tone the cat audio (message signal) rides on. 10 kHz sits well
# above LOWPASS_CUTOFF_HZ (so the lower sideband stays above 0 Hz) and, with
# the message band-limited to LOWPASS_CUTOFF_HZ before modulation, the
# occupied band [fc - cutoff, fc + cutoff] = [2 kHz, 18 kHz] fits under the
# Nyquist limit of *both* target rates (25 kHz at 50 kHz, 250 kHz at
# 500 kHz) -- the same carrier is valid at both without changing it.
CARRIER_FREQ_HZ = 10_000.0

# Cap on the message's bandwidth before modulation, enforced by
# `lowpass_fft`. Cat vocalizations carry effectively no energy above this,
# and it guarantees the AM sidebands (fc +/- bandwidth) never fold past
# either target Nyquist rate or overlap DC.
LOWPASS_CUTOFF_HZ = 8_000.0


def lowpass_fft(signal: np.ndarray, sample_rate: float, cutoff_hz: float) -> np.ndarray:
    """Brick-wall low-pass filter via FFT masking.

    Zeroes out every frequency bin above `cutoff_hz` (both positive and
    negative) and inverse-transforms back to the time domain.

    Args:
        signal: Real-valued input signal.
        sample_rate: Samples per second (Hz).
        cutoff_hz: Frequencies above this are removed.

    Returns:
        The filtered, real-valued signal (same length as `signal`).
    """
    spectrum = np.fft.fft(signal)
    freqs = np.fft.fftfreq(signal.size, d=1.0 / sample_rate)
    spectrum[np.abs(freqs) > cutoff_hz] = 0.0
    return np.fft.ifft(spectrum).real


def am_modulate(
    message: np.ndarray,
    sample_rate: float,
    carrier_freq_hz: float = CARRIER_FREQ_HZ,
    modulation_index: float = 1.0,
) -> np.ndarray:
    """Amplitude-modulate a message signal onto a cosine carrier.

    `s[n] = (1 + modulation_index * m_norm[n]) * cos(2*pi*fc*n/fs)`, where
    `m_norm` is `message` peak-normalized to `[-1, 1]` so `modulation_index`
    directly controls how deep the modulation is (1.0 = standard AM, no
    over-modulation as long as `modulation_index <= 1.0`).

    Args:
        message: Message signal (e.g. resampled, band-limited audio).
        sample_rate: Samples per second (Hz) of `message` == the carrier's
            sample rate (both must share a sample rate to multiply).
        carrier_freq_hz: Carrier frequency, in Hz.
        modulation_index: Modulation depth, typically in `(0, 1]`.

    Returns:
        The modulated signal, same length as `message`.
    """
    if message.size == 0:
        raise ValueError("message must be non-empty")

    peak = np.max(np.abs(message))
    m_norm = message / peak if peak > 0 else message

    n = np.arange(message.size)
    carrier = np.cos(2 * np.pi * carrier_freq_hz * n / sample_rate)
    return (1.0 + modulation_index * m_norm) * carrier


def modulate_at_rate(
    signal: np.ndarray,
    orig_sample_rate: float,
    target_sample_rate: float,
    carrier_freq_hz: float = CARRIER_FREQ_HZ,
    lowpass_cutoff_hz: float = LOWPASS_CUTOFF_HZ,
) -> np.ndarray:
    """Resample, band-limit, and AM-modulate a signal at a target rate.

    Args:
        signal: Message signal at its native sample rate.
        orig_sample_rate: `signal`'s native sample rate, in Hz.
        target_sample_rate: Sample rate to resample+modulate at (e.g.
            50 000 or 500 000).
        carrier_freq_hz: Carrier frequency, in Hz.
        lowpass_cutoff_hz: Message low-pass cutoff before modulation.

    Returns:
        The modulated signal at `target_sample_rate`.
    """
    import librosa

    resampled = librosa.resample(
        np.asarray(signal, dtype=np.float64),
        orig_sr=orig_sample_rate,
        target_sr=target_sample_rate,
    )
    limited = lowpass_fft(resampled, target_sample_rate, lowpass_cutoff_hz)
    return am_modulate(limited, target_sample_rate, carrier_freq_hz)
