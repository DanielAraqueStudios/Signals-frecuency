"""Integration test for `modulate_at_rate`, which needs librosa (resampling).

Skips gracefully if librosa isn't installed or the real 'gato' recording
isn't present -- matching how other folders in this repo keep real-audio
I/O out of the required unit-test path.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("librosa")

from modulation_lab.audio import load_audio
from modulation_lab.modulation import CARRIER_FREQ_HZ, modulate_at_rate

AUDIO_PATH = Path(__file__).parent.parent / "audio_samples" / "gato" / "gato.ogg"

pytestmark = pytest.mark.skipif(not AUDIO_PATH.exists(), reason="gato.ogg not found")


def _load_audio_or_skip():
    try:
        return load_audio(str(AUDIO_PATH))
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"audio backend unavailable: {exc}")


@pytest.mark.parametrize("target_fs", [50_000, 500_000])
def test_modulate_at_rate_sample_count(target_fs):
    signal, orig_sr = _load_audio_or_skip()
    duration_s = signal.size / orig_sr

    modulated = modulate_at_rate(signal, orig_sr, target_fs)

    expected = round(duration_s * target_fs)
    assert abs(modulated.size - expected) <= 1


def test_modulate_at_rate_carrier_present_at_both_rates():
    signal, orig_sr = _load_audio_or_skip()

    for target_fs in (50_000, 500_000):
        modulated = modulate_at_rate(signal, orig_sr, target_fs)
        n = modulated.size
        freqs = np.fft.fftfreq(n, d=1.0 / target_fs)
        magnitude = np.abs(np.fft.fft(modulated)) / (n / 2)
        carrier_peak = magnitude[np.abs(freqs - CARRIER_FREQ_HZ) <= 50].max()
        assert carrier_peak > 0.1
