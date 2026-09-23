import numpy as np

from fir_iir_lab.hilbert_tools import hilbert_envelope
from fir_iir_lab.signals import sample_times


def test_hilbert_envelope_recovers_known_am_envelope():
    fs = 10_000
    t = sample_times(0.5, fs)
    envelope = 2 + np.sin(2 * np.pi * 5 * t)  # slow, known envelope
    carrier = np.sin(2 * np.pi * 500 * t)     # fast carrier
    x = envelope * carrier

    recovered = hilbert_envelope(x)
    steady = slice(200, -200)
    np.testing.assert_allclose(recovered[steady], envelope[steady], atol=0.15)


def test_hilbert_envelope_constant_for_pure_tone():
    fs = 10_000
    t = sample_times(0.2, fs)
    x = np.sin(2 * np.pi * 200 * t)
    envelope = hilbert_envelope(x)
    steady = envelope[100:-100]
    assert np.allclose(steady, 1.0, atol=0.05)
