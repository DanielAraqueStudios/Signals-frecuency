"""Continuous Wavelet Transform (CWT) scalogram computation using
`PyWavelets` (`pywt`) — a dependency new to this repo, not used by any
other `WORK_*` folder yet (see readme.md Requirements).

`pywt` is imported lazily so `vectors.py` and non-wavelet tests stay
importable without it installed, mirroring `audio.py::load_audio`'s
lazy `librosa` import.
"""

from __future__ import annotations

import numpy as np

DEFAULT_WAVELET = "morl"  # Morlet: good time-frequency localization for audio


def cwt_scalogram(
    signal: np.ndarray,
    sample_rate: int,
    wavelet: str = DEFAULT_WAVELET,
    n_scales: int = 64,
    fmin: float = 20.0,
    fmax: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute a CWT energy scalogram (frequency map) of `signal`.

    Scales are chosen so the corresponding pseudo-frequencies span
    `[fmin, fmax]` log-spaced, then converted to `pywt.cwt` scales via
    `pywt.scale2frequency`.

    Args:
        signal: 1-D real signal.
        sample_rate: Samples per second (Hz).
        wavelet: A continuous `pywt` wavelet name (default `"morl"`).
        n_scales: Number of scales/frequency bins to compute.
        fmin: Lowest frequency of interest, in Hz.
        fmax: Highest frequency of interest, in Hz (defaults to
            `sample_rate / 2`, the Nyquist frequency).

    Returns:
        `(energy, frequencies, times)`:
        - `energy`: `(n_scales, len(signal))` array, `|coefficients|**2`.
        - `frequencies`: `(n_scales,)` array of Hz, matching `energy`'s rows.
        - `times`: `(len(signal),)` array of seconds, matching `energy`'s columns.

    Raises:
        ValueError: If `signal` is empty.
    """
    import pywt

    signal = np.asarray(signal, dtype=np.float64)
    if signal.size == 0:
        raise ValueError("signal must be non-empty")

    fmax = sample_rate / 2 if fmax is None else fmax
    frequencies = np.geomspace(fmin, fmax, n_scales)
    scales = pywt.frequency2scale(wavelet, frequencies / sample_rate)

    coefficients, actual_frequencies = pywt.cwt(signal, scales, wavelet, sampling_period=1.0 / sample_rate)
    energy = np.abs(coefficients) ** 2
    times = np.arange(signal.size) / sample_rate
    return energy, actual_frequencies, times
