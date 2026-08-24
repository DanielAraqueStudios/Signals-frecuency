"""Item 2 — 100 Hz sine wave: sampling, DAC-style quantization, aliasing.

Aliasing occurs when a signal is sampled below its Nyquist rate
(``fs < 2 * f_signal``): frequency components above ``fs / 2`` fold back into
the ``[0, fs/2]`` band and appear as a *different, lower* frequency in the
reconstructed signal. For a 100 Hz sine wave, ``fs = 70 Hz`` is below the
200 Hz Nyquist rate and aliases; ``fs = 500 Hz`` and ``fs = 1000 Hz`` are
both comfortably above it and do not. The standard prevention is to satisfy
the sampling theorem (``fs >= 2 * f_signal``) and/or apply an analog
anti-aliasing low-pass filter before sampling to remove content above
``fs / 2`` that the chosen rate cannot represent.
"""

from __future__ import annotations

import numpy as np

SIGNAL_FREQUENCY_HZ = 100.0


def sine_wave(frequency_hz: float, t: np.ndarray, amplitude: float = 1.0) -> np.ndarray:
    """Evaluate ``amplitude * sin(2*pi*f*t)`` at the given time points."""
    return amplitude * np.sin(2 * np.pi * frequency_hz * t)


def sample_signal(
    frequency_hz: float, sample_rate_hz: float, duration_s: float, amplitude: float = 1.0
) -> tuple[np.ndarray, np.ndarray]:
    """Sample a sine wave of ``frequency_hz`` at ``sample_rate_hz``.

    Returns ``(t_samples, values)``.
    """
    t_samples = np.arange(0, duration_s, 1 / sample_rate_hz)
    return t_samples, sine_wave(frequency_hz, t_samples, amplitude)


def quantize_dac(signal: np.ndarray, bits: int = 3) -> np.ndarray:
    """Quantize a signal assumed to be in ``[-1, 1]`` to ``2**bits`` levels.

    This mirrors a simple DAC reconstruction step: normalize to ``[0, 1]``,
    round to the nearest of ``2**bits`` evenly-spaced levels, then rescale
    back to ``[-1, 1]``.
    """
    if bits < 1:
        raise ValueError("bits must be >= 1")
    levels = 2**bits
    normalized = (signal + 1) / 2
    quantized = np.round(normalized * (levels - 1)) / (levels - 1)
    return quantized * 2 - 1


def is_aliased(signal_frequency_hz: float, sample_rate_hz: float) -> bool:
    """True if ``sample_rate_hz`` is below the Nyquist rate for the signal."""
    return sample_rate_hz < 2 * signal_frequency_hz
