# Sampling, Fourier Series & Spectral Analysis Lab

> Part of the [`Signals-frecuency`](../../../../Readme.md) repository — see the root
> README for the full project index.

A Python package covering a set of signal-sampling and spectral-analysis
exercises: sine/triangular/square-wave sampling at several rates, square-wave
construction via a truncated Fourier sine series, an ideal-vs-reconstructed
FFT comparison, and a desktop GUI that runs mean/std/FFT statistics on
animal-sound recordings to study how separable they are.

---

## Table of Contents

- [Scope](#scope)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Sampling & Fourier-series demo](#sampling--fourier-series-demo)
  - [Animal-sound analyzer GUI](#animal-sound-analyzer-gui)
  - [Programmatic use](#programmatic-use)
- [API Reference](#api-reference)
- [Signal Processing Notes](#signal-processing-notes)
- [Testing](#testing)

---

## Scope

This folder implements items 4-9 of the assignment. Items 1-3 (a MATLAB→Python
port, "melodías con los códigos", and the written theoretical homework) are
**not included** — they need source material (the MATLAB code and the
homework question text) that hasn't been supplied yet.

| Item | Description | Where |
|------|-------------|-------|
| 4 | Sample a 3 kHz sine at 1, 3, 6, 10, 30 kHz | `signal_lab.plot_sine_sampling_grid`, `main.py` |
| 5 | Build a square wave from its Fourier series, N = 1, 2, 5, 10 harmonics | `signal_lab.plot_square_construction`, `main.py` |
| 6 | Sample a 10 kHz triangular wave (Vmax=7, Vmin=2) at 30/50/100 kHz + one random rate | `signal_lab.plot_triangular_sampling_grid`, `main.py` |
| 7 | Sample the Fourier-series square wave (N = 1,2,3,5,10) at 1,3,6,10,30 kHz | `signal_lab.plot_square_sampling_grid`, `main.py` |
| 8 | Mean/std/FFT on animal-sound audio; discuss statistical separability | `animal_analyzer/`, `run_animal_gui.py` |
| 9 | FFT of an ideal square wave vs. its 10-harmonic reconstruction | `signal_lab.plot_fft_comparison`, `main.py` |

## Project Structure

```
WORK_THREE/
├── signal_lab/                 Core package: items 4, 5, 6, 7, 9
│   ├── __init__.py             Public exports
│   ├── waveforms.py            Sine / square (ideal + Fourier series) / triangular synthesis
│   ├── spectral.py             FFT + descriptive statistics (shared with animal_analyzer)
│   └── plotting.py             Matplotlib figure assembly, one function per item
├── animal_analyzer/             Item 8: audio statistics + GUI
│   ├── __init__.py
│   ├── core.py                 Audio loading, 3s windowing, FFT/mean/std, separability report
│   └── gui.py                  customtkinter desktop app (3 category tabs + summary tab)
├── audio_samples/                Drop recordings here before using the GUI
│   ├── gato/
│   ├── perro/
│   └── gallo/
├── tests/
│   ├── test_waveforms.py
│   ├── test_spectral.py
│   └── test_animal_analyzer.py
├── report/                       IEEE-conference LaTeX write-up of item 8
│   ├── main.tex                 Preamble + \input of every section
│   ├── secciones/                One .tex file per report section
│   └── figuras/                  Drop exported GUI plots here (see report/main.tex)
├── main.py                      Entry point: renders items 4, 5, 6, 7, 9
├── run_animal_gui.py            Entry point: launches the item 8 GUI
├── sample.tex                    Original draft report (superseded by report/main.tex)
└── readme.md
```

## Requirements

| Dependency | Purpose | Needed for |
|---|---|---|
| Python ≥ 3.9 | Runtime | Everything |
| NumPy | Vectorized signal synthesis & FFT | Everything |
| SciPy | Ideal square/triangular waveform generators | `signal_lab` |
| Matplotlib | Waveform/spectrum visualization | `main.py`, GUI plots |
| pytest | Test suite | Development |
| customtkinter | Desktop GUI widgets | `run_animal_gui.py` only |
| librosa | Audio file loading (wav/mp3/flac/ogg/m4a) | `run_animal_gui.py` only |
| soundfile | Audio backend used by librosa | `run_animal_gui.py` only |

`signal_lab` and its tests have **no GUI/audio dependencies** — `librosa` is
imported lazily inside `animal_analyzer.core.load_audio`, so the rest of the
project stays importable and testable without it installed.

## Installation

```bash
pip install numpy scipy matplotlib pytest
# Only needed for the item 8 GUI:
pip install customtkinter librosa soundfile
```

## Usage

### Sampling & Fourier-series demo

```bash
cd WORK_THREE
python main.py
```

Opens one Matplotlib figure per exercise (items 4, 5, 6, 7, 9) — five
figures in total, most stacking several subplots (one per harmonic count or
sampling rate being compared).

### Animal-sound analyzer GUI

```bash
cd WORK_THREE
python run_animal_gui.py
```

Copy your Gato/Perro/Gallo recordings into `audio_samples/<category>/`
(the folders exist as placeholders), then use the "Cargar Gato/Perro/Gallo"
buttons to pick a file from there and "Analizar Audios" to compute, per
category, the waveform (first 3 s), its FFT, dominant frequency, mean, and
standard deviation. A fourth **📊 Resumen** tab reports a pairwise
statistical-separability score once at least two categories are analyzed
(see [Signal Processing Notes](#signal-processing-notes)).

The GUI is scoped to these three animal-sound categories as a concrete case
study for item 8's broader question ("¿se puede diferenciar voces,
instrumentos y animales?"); extending it to voice/instrument recordings
would mean adding more category buttons/folders following the same pattern.

### Programmatic use

```python
from signal_lab import angular_frequency, square_wave_fourier, sample_times, compute_fft

w0 = angular_frequency(100.0)
t = sample_times(duration_s=0.03, sample_rate=50_000)
x = square_wave_fourier(t, w0, num_harmonics=10)
freqs, magnitude = compute_fft(x, sample_rate=50_000)
```

```python
from animal_analyzer.core import load_audio, analyze_audio, compare_categories

signal, fs = load_audio("audio_samples/gato/gato1.wav")
result = analyze_audio(signal, fs)  # windows to the first 3 s internally
print(result["dominant_frequency_hz"], result["mean"], result["std"])
```

## API Reference

### `signal_lab.waveforms`

| Function | Description |
|---|---|
| `angular_frequency(frequency_hz)` | Hz → rad/s |
| `sample_times(duration_s, sample_rate)` | Builds a `[0, duration_s)` time axis |
| `sine_wave(t, frequency_hz, amplitude=1.0)` | Pure sine |
| `square_wave_fourier(t, w0, num_harmonics, amplitude=1.0)` | Square wave from a truncated odd-harmonic sine series |
| `square_wave_ideal(t, frequency_hz, amplitude=1.0)` | Mathematically ideal (infinite-bandwidth) square wave |
| `triangular_wave(t, frequency_hz, v_max, v_min)` | Triangular wave offset to swing between `v_min` and `v_max` |

### `signal_lab.spectral`

| Function | Description |
|---|---|
| `compute_fft(signal, sample_rate)` | Single-sided, amplitude-normalized FFT: `(frequencies, magnitude)` |
| `dominant_frequency(frequencies, magnitude)` | Frequency of the largest non-DC peak |
| `signal_stats(signal)` | `{"mean": ..., "std": ...}` |

### `signal_lab.plotting`

One function per exercise — `plot_sine_sampling_grid`, `plot_square_construction`,
`plot_triangular_sampling_grid`, `plot_square_sampling_grid`, `plot_fft_comparison`
— each returning an assembled (not shown/saved) `matplotlib.figure.Figure`.

### `animal_analyzer.core`

| Function | Description |
|---|---|
| `load_audio(path)` | Loads a mono file at its native sample rate (lazy `librosa` import) |
| `analysis_window(signal, sample_rate, window_s=3.0)` | Truncates to the first `window_s` seconds |
| `analyze_audio(signal, sample_rate, window_s=3.0)` | Windows, then computes FFT + mean + std + dominant frequency |
| `separability_score(result_a, result_b)` | `\|Δ dominant frequency\| / (std_a + std_b)` |
| `compare_categories(results)` | Plain-text per-category stats + pairwise separability verdicts |

## Signal Processing Notes

- **Aliasing (item 4)**: a 3 kHz sine needs a sampling rate ≥ 6 kHz (Nyquist)
  to be reconstructible without ambiguity. The 1 kHz and 3 kHz cases in the
  demo are deliberately below Nyquist and are labeled "(ALIASING)" in their
  subplot legend.
- **Gibbs phenomenon (item 5)**: as with `WORK_TWO`, no finite number of
  harmonics eliminates the ~9% overshoot at a square wave's discontinuities;
  more harmonics narrow the ripple without shrinking its peak.
- **Triangular wave amplitude (item 6)**: the assignment states both
  "amplitude 9" and `Vmax=7`/`Vmin=2` (a 5-unit peak-to-peak span) — these
  are inconsistent as literally stated. `triangular_wave` treats `v_max`/
  `v_min` as authoritative and builds the wave to swing exactly between
  them; adjust `TRIANGLE_V_MAX`/`TRIANGLE_V_MIN` in `main.py` if a different
  reading of "amplitude 9" was intended.
- **Random sampling rate (item 6)**: chosen once via a seeded
  `numpy.random.default_rng` (see `main.py`) so the demo is reproducible
  rather than different on every run; it's drawn from a band above the
  10 kHz signal's Nyquist rate.
- **Ideal vs. N-harmonic FFT (item 9)**: the ideal square wave's spectrum has
  a line at every odd harmonic, each decaying as `1/n`; the 10-harmonic
  reconstruction's spectrum matches it exactly at harmonics 1-19 (n = 2·10-1)
  and then has **no** content beyond that — the truncation is visible in the
  frequency domain as missing higher-order lines, which is the spectral
  counterpart of the Gibbs ripple visible in the time domain.
- **Statistical separability (item 8)**: `separability_score` is a rough,
  signal-processing analogue of a t-statistic — the gap between two
  categories' dominant frequencies, normalized by how spread out (noisy)
  each one's waveform is. A large gap relative to the combined spread means
  the categories are easy to tell apart from mean/std/FFT alone; heavy
  overlap in std with a small frequency gap means they likely aren't. This
  is a coarse heuristic (a single dominant peak + global std), not a
  substitute for a trained classifier — real voice/instrument/animal audio
  has richer spectral structure (harmonics, formants, transients) that a
  single peak comparison doesn't capture.

## Testing

```bash
python -m pytest tests/ -v
```

25 tests cover:
- `signal_lab.waveforms`: closed-form checks for sine/square/triangular
  synthesis, the `num_harmonics < 1` error, harmonic-count convergence, and
  amplitude scaling.
- `signal_lab.spectral`: FFT peak recovery for a known-frequency sine, DC
  rejection in `dominant_frequency`, and `signal_stats` against NumPy directly.
- `animal_analyzer.core`: the 3 s windowing rule, `analyze_audio` end-to-end
  on a synthetic tone, and `separability_score`/`compare_categories` behavior.

`load_audio` (real file I/O) and `animal_analyzer.gui` (Tk widgets) are
intentionally excluded from automated tests, the same way `WORK_TWO` excludes
its plotting module — they wrap already-tested logic around external
I/O/UI that isn't meaningfully unit-testable.
