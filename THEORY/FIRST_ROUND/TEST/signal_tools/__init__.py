"""signal_tools — sampling, quantization, and FFT utilities for the TEST project (THEORY/FIRST_ROUND/TEST).

Three small, independently testable modules, mirroring the split used in
WORK_THREE's ``signal_lab``:

- ``csv_signal``: load a recorded signal from CSV, split it into fixed-size
  segments, and extract each segment's dominant frequency (item 1).
- ``sampling``: synthesize a sine wave, sample it at a given rate, and
  quantize it with a simple DAC-style rounding algorithm (item 2).
- ``audio_fft``: load a WAV file and compute its single-sided FFT magnitude
  spectrum, to compare real-world sound sources (item 3).

Plotting lives in ``plotting.py`` and is intentionally excluded from the
`__init__` re-export list kept minimal below — import it directly when needed.
"""

from .csv_signal import load_csv_signal, segment_signal, dominant_frequency
from .sampling import sine_wave, sample_signal, quantize_dac, is_aliased
from .audio_fft import load_wav, compute_fft_spectrum

__all__ = [
    "load_csv_signal",
    "segment_signal",
    "dominant_frequency",
    "sine_wave",
    "sample_signal",
    "quantize_dac",
    "is_aliased",
    "load_wav",
    "compute_fft_spectrum",
]
