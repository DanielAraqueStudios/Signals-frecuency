import numpy as np

from conv_lab.audio import segment


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
