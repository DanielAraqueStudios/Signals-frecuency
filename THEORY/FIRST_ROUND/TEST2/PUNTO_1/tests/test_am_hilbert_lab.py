"""Deterministic tests using synthetic AM signals with known parameters."""

from __future__ import annotations

import numpy as np

from am_hilbert_lab import (
    apply_filter,
    design_fir_bandpass,
    design_fir_lowpass,
    design_iir_bandpass,
    design_iir_lowpass,
    hilbert_envelope,
    single_sided_fft,
)
from am_hilbert_lab.spectrum import dominant_frequency

FS = 200_000.0
DURATION_S = 0.02
T = np.arange(0, DURATION_S, 1 / FS)
CARRIER_HZ = 20_000.0
MESSAGE_HZ = 3_000.0
CARRIER_AMPLITUDE = 5.0


def synthetic_am_signal():
    message = 1.0 + 0.5 * np.sin(2 * np.pi * MESSAGE_HZ * T)
    return message * CARRIER_AMPLITUDE * np.sin(2 * np.pi * CARRIER_HZ * T)


def test_single_sided_fft_finds_carrier():
    x = CARRIER_AMPLITUDE * np.sin(2 * np.pi * CARRIER_HZ * T)
    freqs, mag = single_sided_fft(x, FS)
    peak_freq = freqs[np.argmax(mag)]
    assert abs(peak_freq - CARRIER_HZ) < 1 / DURATION_S


def test_dominant_frequency_matches_known_tone():
    x = np.sin(2 * np.pi * MESSAGE_HZ * T)
    freq = dominant_frequency(x, FS)
    assert abs(freq - MESSAGE_HZ) < 1 / DURATION_S


def test_hilbert_envelope_recovers_am_message():
    x = synthetic_am_signal()
    envelope = hilbert_envelope(x)
    # Envelope should track 1 + 0.5*sin(2*pi*f_msg*t) * CARRIER_AMPLITUDE.
    expected = (1.0 + 0.5 * np.sin(2 * np.pi * MESSAGE_HZ * T)) * CARRIER_AMPLITUDE
    assert np.corrcoef(envelope, expected)[0, 1] > 0.99


def test_hilbert_envelope_constant_for_pure_tone():
    x = CARRIER_AMPLITUDE * np.sin(2 * np.pi * CARRIER_HZ * T)
    envelope = hilbert_envelope(x)
    # Ignore edge transients from the Hilbert transform.
    steady = envelope[100:-100]
    assert np.std(steady) / np.mean(steady) < 0.05
    assert abs(np.mean(steady) - CARRIER_AMPLITUDE) < 0.1


def test_fir_lowpass_extracts_message_from_envelope():
    x = synthetic_am_signal()
    envelope = hilbert_envelope(x)
    b = design_fir_lowpass(5_000, FS, order=100)
    filtered = apply_filter(b, [1.0], envelope)
    freq = dominant_frequency(filtered - filtered.mean(), FS)
    assert abs(freq - MESSAGE_HZ) < 200


def test_iir_lowpass_extracts_message_from_envelope():
    x = synthetic_am_signal()
    envelope = hilbert_envelope(x)
    b, a = design_iir_lowpass(5_000, FS, order=4)
    filtered = apply_filter(b, a, envelope)
    freq = dominant_frequency(filtered - filtered.mean(), FS)
    assert abs(freq - MESSAGE_HZ) < 200


def test_fir_bandpass_at_message_freq_does_not_recover_sine_from_raw_am():
    """A filter centered at f_message applied to the RAW AM signal should NOT
    reproduce a sine at f_message, because the AM signal has no spectral
    content there -- only at f_carrier +/- f_message."""
    x = synthetic_am_signal()
    b = design_fir_bandpass(MESSAGE_HZ - 500, MESSAGE_HZ + 500, FS, order=50)
    out = apply_filter(b, [1.0], x)
    # The output should not settle into a clean sine at f_message: unlike a
    # true single-tone passband, its RMS stays far below the carrier's.
    assert np.sqrt(np.mean(out**2)) < 0.5 * CARRIER_AMPLITUDE / np.sqrt(2)


def test_iir_bandpass_at_message_freq_does_not_recover_sine_from_raw_am():
    x = synthetic_am_signal()
    b, a = design_iir_bandpass(MESSAGE_HZ - 500, MESSAGE_HZ + 500, FS, order=4)
    out = apply_filter(b, a, x)
    assert np.max(np.abs(out)) < 0.5 * CARRIER_AMPLITUDE
