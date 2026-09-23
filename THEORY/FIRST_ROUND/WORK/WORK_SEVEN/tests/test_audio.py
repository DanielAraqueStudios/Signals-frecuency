from pathlib import Path

import numpy as np
import pytest

from avg_filter_lab.audio import load_audio, segment

AUDIO_PATH = Path(__file__).parent.parent / "audio_samples" / "gato" / "gato.ogg"


def test_segment_slices_by_time():
    signal = np.arange(1000.0)
    sample_rate = 100  # 10 s total
    out = segment(signal, sample_rate, duration_s=1.0, start_s=2.0)
    np.testing.assert_array_equal(out, signal[200:300])


def test_segment_clamped_to_available_length():
    signal = np.arange(50.0)
    sample_rate = 100
    out = segment(signal, sample_rate, duration_s=1.0, start_s=0.0)
    assert out.size == 50


@pytest.mark.skipif(not AUDIO_PATH.exists(), reason="cat audio sample not present")
def test_load_audio_returns_mono_signal_and_sample_rate():
    signal, sample_rate = load_audio(str(AUDIO_PATH))
    assert signal.ndim == 1
    assert sample_rate > 0
