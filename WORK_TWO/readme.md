# Fourier Square-Wave Sampling

> Part of the [`Signals-frecuency`](../Readme.md) repository — see the root
> README for the full project index.

A Python package that reconstructs a **square wave from its Fourier sine
series** and visualizes how the reconstruction looks under different
sampling rates. Built as a signal-processing personal exercise exploring
Gibbs phenomenon and the sampling theorem.

Each figure sums the first *N* odd harmonics of a 3 Hz fundamental
(`w0 = 6*pi`), weighted by `1/n` per the standard square-wave Fourier
series, then overlays both the continuous reconstruction and its discrete
samples at a given sampling rate — making it easy to see that the Gibbs
overshoot near each discontinuity persists regardless of harmonic count,
while sample density changes independently with the sampling rate.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Run the demo](#run-the-demo)
  - [Programmatic use](#programmatic-use)
- [API Reference](#api-reference)
- [Signal Processing Notes](#signal-processing-notes)
- [Testing](#testing)

---

## Overview

A square wave of angular frequency `w0` can be approximated by summing its
odd harmonics:

```
x(t) = (4/pi) * sum_{n odd} sin(n*w0*t) / n
```

This package provides a clean, tested, vectorized (NumPy-based)
implementation split into independently reusable functions — angular
frequency conversion, time-axis generation, and series synthesis — plus a
Matplotlib visualization that grids reconstructions (by harmonic count)
against a chosen sampling rate.

## Project Structure

```
WORK_TWO/
├── fourier_square/            Core package
│   ├── __init__.py            Public exports
│   ├── synthesis.py           Fourier series math (backend)
│   └── plotting.py            Matplotlib figure assembly
├── tests/
│   └── test_synthesis.py      Unit tests (pytest) for the backend
├── main.py                    Entry point: renders one figure per sampling rate
└── readme.md
```

| Module                          | Responsibility                                              |
|----------------------------------|----------------------------------------------------------------|
| `fourier_square/synthesis.py`    | Angular frequency, time axis, and Fourier series synthesis (single source of truth) |
| `fourier_square/plotting.py`     | Builds the per-sampling-rate comparison figure from synthesized data |
| `main.py`                        | Renders and shows one figure per configured sampling rate      |
| `tests/test_synthesis.py`        | Correctness checks for every synthesis function                |

## Requirements

| Dependency  | Purpose                     |
|-------------|-------------------------------|
| Python ≥ 3.9 | Runtime                     |
| NumPy       | Vectorized signal synthesis  |
| Matplotlib  | Waveform visualization        |
| pytest      | Running the test suite (optional) |

## Installation

```bash
pip install numpy matplotlib pytest
```

## Usage

### Run the demo

```bash
cd WORK_TWO
python main.py
```

This opens one figure per configured sampling rate (`1, 2, 3, 6, 30 kHz` by
default), each stacking subplots for `N = 1, 2, 3, 5, 10` harmonics.

### Programmatic use

```python
from fourier_square import angular_frequency, fourier_square_wave, sample_times

w0 = angular_frequency(3.0)          # 3 Hz fundamental -> rad/s
t = sample_times(duration_s=1.0, sample_rate=1000)
f_t = fourier_square_wave(t, w0, num_harmonics=10)
```

## API Reference

### `angular_frequency(frequency_hz) -> float`
Converts an ordinary frequency (Hz) to an angular frequency (rad/s).

### `sample_times(duration_s, sample_rate) -> np.ndarray`
Builds a time axis sampled at `sample_rate` Hz over `duration_s` seconds.

### `fourier_square_wave(t, w0, num_harmonics) -> np.ndarray`
Reconstructs a unit-amplitude square wave by summing the first
`num_harmonics` odd harmonics of `w0`, each weighted by `1/n`. Raises
`ValueError` if `num_harmonics < 1`.

### `plot_sampling_rate_grid(w0, duration_s, harmonics_list, sample_rate) -> plt.Figure`
Builds a stacked-subplot figure — one subplot per entry in
`harmonics_list` — comparing the reconstructed signal against its samples
at `sample_rate`.

### `DEFAULT_FUNDAMENTAL_HZ`, `DEFAULT_DURATION_S`
Default fundamental frequency (3 Hz, i.e. `w0 = 6*pi`) and time window
(1.0 s) used by `main.py`.

## Signal Processing Notes

- **Odd harmonics only**: a square wave's Fourier series has no
  even-harmonic terms; each included harmonic `n` is weighted `1/n`, so
  higher harmonics contribute progressively less amplitude but sharpen the
  edges.
- **Gibbs phenomenon**: no finite partial sum eliminates the ~9% overshoot
  at a discontinuity — increasing `num_harmonics` narrows the ripple
  without shrinking its peak, which is why the higher-N subplots still
  show overshoot near the edges.
- **Sampling rate vs. reconstruction accuracy**: the sampling rate only
  controls how densely the (already continuous, closed-form) reconstructed
  signal is evaluated and marked with sample points — it does not affect
  the series itself, since no analog-to-digital aliasing step is being
  simulated here.
- **Vectorization**: time-axis evaluation uses NumPy array operations
  rather than per-sample Python loops; only the harmonic summation (at
  most a few dozen terms) uses a Python `for` loop, which is negligible
  next to the vectorized per-sample work it wraps.

## Testing

```bash
python -m pytest tests/test_synthesis.py -v
```

9 tests validate:
- Hz → rad/s conversion and the documented default fundamental
- Time-axis length and spacing
- Single-harmonic output equals a scaled sine
- Output shape matches the input time axis
- `num_harmonics < 1` raises `ValueError`
- More harmonics converge toward the ideal `+1` plateau away from a
  discontinuity
- Half-period antisymmetry (`f(t + T/2) = -f(t)`), a property of
  odd-harmonic-only series

Plotting (`fourier_square/plotting.py`) is intentionally excluded from
automated testing since it only arranges Matplotlib figures around
already-tested data.
