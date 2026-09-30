"""Tests for the FFT-carrier-measurement -> Hilbert -> cutoff-selection
pipeline order in decode_lab.envelope."""

from __future__ import annotations

import numpy as np

from decode_lab.envelope import am_envelope, choose_cutoff_hz, measure_carrier_hz

SAMPLE_RATE_HZ = 53730.0


def test_measure_carrier_hz_recovers_known_frequency():
    fs = SAMPLE_RATE_HZ
    duration_s = 0.5
    t = np.arange(int(fs * duration_s)) / fs
    true_carrier = 997.0
    signal = np.cos(2 * np.pi * true_carrier * t)

    measured = measure_carrier_hz(signal, fs)
    assert abs(measured - true_carrier) < 5.0


def test_choose_cutoff_hz_stays_between_symbol_rate_and_carrier():
    symbol_rate_hz = 1.0 / 0.015  # 66.7 Hz
    for carrier in (997.0, 1000.0, 1003.0):
        cutoff = choose_cutoff_hz(carrier, symbol_rate_hz)
        assert cutoff > symbol_rate_hz
        assert cutoff < carrier


def test_am_envelope_returns_envelope_carrier_and_cutoff():
    fs = SAMPLE_RATE_HZ
    t = np.arange(int(fs * 0.2)) / fs
    signal = 5.0 * np.cos(2 * np.pi * 1000.0 * t)

    envelope, carrier_hz, cutoff_hz = am_envelope(signal, fs)
    assert envelope.shape == signal.shape
    assert abs(carrier_hz - 1000.0) < 5.0
    assert cutoff_hz > 0
    # constant-amplitude carrier -> envelope should settle near 5.0 away from edges
    assert abs(envelope[len(envelope) // 2] - 5.0) < 0.5
