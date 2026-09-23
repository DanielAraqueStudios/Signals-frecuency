# Wavelet & Hilbert Analysis Lab

> Part of the [`Signals-frecuency`](../../../../Readme.md) repository — see the root
> README for the full project index.

Tarea 2: continuous-wavelet-transform (CWT) energy maps of a real audio
recording, a set of six fixed correlation vectors slid across that same
audio to build a 100-element output vector, and CWT scalograms of two voice
recordings ("3 voces diferentes" in the assignment text).

---

## Table of Contents

- [Scope](#scope)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Signal Processing Notes](#signal-processing-notes)
- [Testing](#testing)

---

## Scope

This folder implements Tarea 2 of the assignment:

| Part | Description | Where |
|------|-------------|-------|
| 1 (wavelet spectrum) | CWT energy map (frequency-vs-time) of the 'gato' recording | `wavelet_lab/wavelets.py`, `main.py` |
| 1 (vectors) | Six correlation vectors slid across the cat audio to build a 100-element output vector | `wavelet_lab/vectors.py`, `main.py` |
| 2 (3 voces) | CWT scalograms for each available voice recording | `wavelet_lab/wavelets.py`, `main.py` |

**Only 2 voice recordings exist in this repo** (`WORK_THREE/audio_samples/persona1/`
and `persona2/`) — a 3rd voice was never supplied. This folder analyzes the
two that exist and does not fabricate a third; see
[Signal Processing Notes](#signal-processing-notes) for detail (the same
honesty convention `WORK_THREE/readme.md` uses for its own missing items).

## Project Structure

```
WORK_SIX/
├── wavelet_lab/
│   ├── audio.py           load_audio (lazy librosa import, mirrors WORK_FOUR)
│   ├── wavelets.py         cwt_scalogram: CWT energy map via pywt (lazy import)
│   ├── vectors.py           VECTORS registry + sliding_correlation + correlation_vector_100
│   ├── plotting.py          plot_scalogram, plot_correlation_vector
│   └── __init__.py          Public exports
├── audio_samples/            Local copies of the cat + two voice recordings
│   ├── gato/                 copy of WORK_THREE's/WORK_FOUR's cat recording
│   ├── persona1/              copy of WORK_THREE's persona1 recording
│   └── persona2/              copy of WORK_THREE's persona2 recording
├── tests/
│   ├── test_vectors.py       Deterministic, hand-computable correlation checks
│   └── test_wavelets.py       Shape/range/energy checks on a synthetic tone
├── output/                    wavelet_*.png, correlation_vector_100.{png,npy,csv} (gitignored, not committed)
├── main.py                    Entry point
└── readme.md
```

## Requirements

| Dependency | Purpose | Needed for |
|---|---|---|
| Python ≥ 3.9 | Runtime | Everything |
| NumPy | Vectorized signal ops | Everything |
| Matplotlib | Scalogram / vector visualization | `main.py` |
| pytest | Test suite | Development |
| librosa | Audio file loading (wav/ogg) | `main.py`, `wavelet_lab.audio` only |
| soundfile | Audio backend used by librosa | `main.py`, `wavelet_lab.audio` only |
| **PyWavelets (`pywt`)** | **Continuous Wavelet Transform** — new to this repo, not used by any other `WORK_*` folder | `main.py`, `wavelet_lab.wavelets` only |

`wavelet_lab.vectors` and its tests have **no audio/wavelet dependencies** —
both `librosa` (in `wavelet_lab.audio`) and `pywt` (in `wavelet_lab.wavelets`)
are imported lazily, so the vector-correlation logic stays importable and
testable without either installed.

## Installation

```bash
pip install numpy matplotlib pytest
# Needed for main.py (audio loading + wavelet transform):
pip install librosa soundfile PyWavelets
```

## Usage

```bash
cd WORK_SIX
python main.py
```

Prints sample counts and the 100-element vector's min/max, then saves (and,
unless disabled, shows) five figures to `output/`:
`wavelet_gato.png`, `wavelet_persona1.png`, `wavelet_persona2.png`,
`correlation_vector_100.png`, plus `correlation_vector_100.{npy,csv}` holding
the raw 100-element vector.

### Programmatic use

```python
from wavelet_lab import load_audio, cwt_scalogram, correlation_vector_100

signal, sr = load_audio("audio_samples/gato/gato.ogg")
energy, frequencies, times = cwt_scalogram(signal, sr)   # (n_scales, n_samples) energy map
output_vector = correlation_vector_100(signal)             # 100-element array
```

## API Reference

### `wavelet_lab.audio`

| Function | Description |
|---|---|
| `load_audio(path)` | Loads a mono file at its native sample rate (lazy `librosa` import) |

### `wavelet_lab.wavelets`

| Function | Description |
|---|---|
| `cwt_scalogram(signal, sample_rate, wavelet="morl", n_scales=64, fmin=20.0, fmax=None)` | CWT energy map: `(energy, frequencies, times)` (lazy `pywt` import) |

### `wavelet_lab.vectors`

| Name | Description |
|---|---|
| `VECTORS` | `dict[str, np.ndarray]` — the six fixed vectors from the assignment (`Vector1..Vector6`) |
| `sliding_correlation(vector, signal, n_values)` | Slides `vector` across `signal`, one dot product per position |
| `correlation_vector_100(signal)` | Builds the 100-element output vector across all six `VECTORS` |

### `wavelet_lab.plotting`

| Function | Description |
|---|---|
| `plot_scalogram(energy, frequencies, times, title)` | CWT energy map as a pcolormesh (log-frequency axis) |
| `plot_correlation_vector(output_vector, block_boundaries, vector_names)` | 100-element output vector, shaded by which `VECTORn` produced each block |

## Signal Processing Notes

- **Wavelet choice**: `cwt_scalogram` defaults to the Morlet wavelet
  (`"morl"`), a standard choice for audio time-frequency analysis because of
  its good simultaneous time/frequency localization; any continuous `pywt`
  wavelet name can be passed instead.
- **Only 2 of 3 requested voices**: the assignment asks for wavelet analysis
  "con 3 voces diferentes", but this repo only has two voice recordings
  (`persona1`, `persona2`, both from `WORK_THREE`). `main.py` runs the
  scalogram for both that exist and stops there — a fabricated third
  recording would misrepresent real data as something it isn't, so none is
  synthesized.
- **Interpretation of the 100-element output vector**: the assignment gives
  a single worked example per vector — e.g. `Vector1` (all ones, length 10)
  dotted against the *first* 10 audio samples, summed, stored — but then asks
  for a **100-element** output vector from only 6 fixed-length vectors, and
  six single dot products can only ever produce six numbers. The
  implemented interpretation treats the worked example as a **lag-0 sliding
  correlation** and generalizes it to a full sliding dot product (discrete
  cross-correlation, "valid" mode): `sliding_correlation` computes
  `sum(vector[k] * signal[start + k])` for `start = 0, 1, 2, ...`, so its
  first output is exactly the assignment's worked example. `correlation_vector_100`
  then splits the 100 output slots as evenly as possible across the six
  vectors (`100 = 6·16 + 4`, so `Vector1..Vector4` each contribute 17
  sliding-correlation values and `Vector5`/`Vector6` each contribute 16),
  and concatenates the six blocks in `Vector1..Vector6` order. This choice
  is implemented in `wavelet_lab/vectors.py::_split_counts` and documented
  there in detail — it is one reasonable reading of an ambiguous spec, not
  the only possible one, and is easy to swap for a different split if a
  stricter reading is intended.
- **pywt availability**: `pywt` was not installed in the development
  environment when this folder was authored; it was installed for this
  session (`pip install PyWavelets`, resolved to `1.10.0`). Both the test
  suite and a full `python main.py` run against the real `gato`/`persona1`/
  `persona2` audio files were executed successfully, producing all five
  figures plus the 100-element vector under `output/`.

## Testing

```bash
python -m pytest tests/ -v
```

14 tests cover:
- `wavelet_lab.vectors`: exact vector shapes/values, `_split_counts`'
  100/6 distribution, `sliding_correlation` against hand-computable
  synthetic arrays (including the assignment's own worked example and an
  all-zero-vector edge case), `correlation_vector_100`'s length and its
  first two output values, and the short-signal `ValueError`.
- `wavelet_lab.wavelets`: `cwt_scalogram`'s output shapes, that returned
  frequencies stay within the requested `fmin`/`fmax` band, non-negative
  energy, the empty-signal `ValueError`, and that a pure 50 Hz test tone's
  energy peaks near 50 Hz. Skipped automatically (`pytest.importorskip`) if
  `pywt` is not installed.

`load_audio` (real file I/O) is intentionally excluded from automated
tests, the same way `WORK_THREE`/`WORK_FOUR` exclude theirs — it wraps
already-tested logic around external file I/O that isn't meaningfully
unit-testable.
