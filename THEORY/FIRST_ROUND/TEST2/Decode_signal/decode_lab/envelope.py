"""AM envelope recovery, in the order: (1) FFT to measure the real
modulated carrier frequency, (2) Hilbert transform of the RAW signal to
get the envelope, (3) derive the lowpass cutoff frequency from the
measured carrier and the known symbol rate, and smooth the envelope with
it.

No bandpass filter is applied to the raw signal before the Hilbert
transform: an earlier version tried that as a denoising step and it broke
badly on 12 of the 13 real files (see readme "Signal Processing Notes"
for the full story) -- a narrow pre-Hilbert bandpass is fragile, and it
was never necessary for correctness in the first place.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, hilbert

NOMINAL_CARRIER_HZ = 1000.0
CARRIER_SEARCH_HALF_WINDOW_HZ = 100.0
SYMBOL_RATE_HZ = 1.0 / 0.015  # 66.7 Hz, matches symbols.SYMBOL_DURATION_S


def measure_carrier_hz(amplitude: np.ndarray, sample_rate: float) -> float:
    """Step 1: FFT peak near the nominal 1000 Hz carrier, per file.

    The real carrier drifts slightly from file to file (Muestra01's own
    carrier measured ~997 Hz, not exactly 1000) -- measuring it per file,
    rather than assuming a fixed value, is what lets the cutoff frequency
    below be chosen correctly for each file.
    """
    n = len(amplitude)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    spectrum = np.abs(np.fft.rfft(amplitude))
    band = (freqs >= NOMINAL_CARRIER_HZ - CARRIER_SEARCH_HALF_WINDOW_HZ) & \
           (freqs <= NOMINAL_CARRIER_HZ + CARRIER_SEARCH_HALF_WINDOW_HZ)
    return float(freqs[band][np.argmax(spectrum[band])])


def choose_cutoff_hz(carrier_hz: float, symbol_rate_hz: float = SYMBOL_RATE_HZ,
                      above_symbol_rate_factor: float = 4.0,
                      below_carrier_fraction: float = 0.3) -> float:
    """Step 3: pick the envelope-smoothing lowpass cutoff from the measured
    carrier and the symbol rate, instead of a hardcoded constant.

    Must sit well above the symbol rate (so transitions between
    consecutive 15 ms symbols survive) and well below the carrier (so
    carrier ripple is removed): take the smaller of
    `above_symbol_rate_factor * symbol_rate_hz` and
    `below_carrier_fraction * carrier_hz`, which for the real data's
    measured ~997-1000 Hz carrier and 66.7 Hz symbol rate lands at
    `4 * 66.7 = 266.8 Hz` (comfortably between the two bounds).
    """
    return min(above_symbol_rate_factor * symbol_rate_hz, below_carrier_fraction * carrier_hz)


def am_envelope(amplitude: np.ndarray, sample_rate: float) -> tuple[np.ndarray, float, float]:
    """Steps 1-3 wired together. Returns `(envelope, carrier_hz, cutoff_hz)`
    so the measured/derived parameters are visible to the caller, not
    hidden inside the function.
    """
    carrier_hz = measure_carrier_hz(amplitude, sample_rate)
    cutoff_hz = choose_cutoff_hz(carrier_hz)

    analytic_magnitude = np.abs(hilbert(amplitude))
    nyquist = sample_rate / 2.0
    b, a = butter(4, cutoff_hz / nyquist, btype="low")
    envelope = filtfilt(b, a, analytic_magnitude)

    return envelope, carrier_hz, cutoff_hz
