# DTMF Dialer

> Part of the [`Signals-frecuency`](../Readme.md) repository — see the root
> README for the full project index.

A Python package that synthesizes, exports, and plays **DTMF
(Dual-Tone Multi-Frequency)** dial tones — the audio signal a telephone
keypad produces when a digit is pressed. Built as a signal-processing
personal exercise in signal processing.

Each digit is generated as the sum of two sinusoids (a *low-group* and a
*high-group* frequency, per the ITU-T Q.23 standard), assembled into a
mono 16-bit PCM waveform, written to a `.wav` file, and played back. The
package ships with both a **CLI** and a **PyQt6 desktop GUI**, both built on
the same backend module — the phone number is always supplied by the user
(CLI argument/prompt or GUI text field), never hardcoded.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [CLI](#cli)
  - [GUI](#gui)
  - [Programmatic use](#programmatic-use)
- [API Reference](#api-reference)
- [DTMF Frequency Table](#dtmf-frequency-table)
- [Signal Processing Notes](#signal-processing-notes)
- [Testing](#testing)
- [Platform Notes](#platform-notes)

---

## Overview

DTMF encodes each keypad symbol as **two simultaneous sine tones** — one
from a low-frequency group (697–941 Hz) and one from a high-frequency group
(1209–1477 Hz) — mixed into a single audio signal. This is the same scheme
used by real telephone networks for touch-tone dialing.

This package provides a clean, tested, vectorized (NumPy-based)
implementation split into independently reusable functions: tone synthesis,
silence generation, sequence assembly, WAV export, and playback — plus a
threaded desktop GUI that visualizes the generated waveform, including a
real-time playhead synced to audio playback.

## Project Structure

```
WORK_ONE/
├── dtmf_dialer/                 Core package
│   ├── __init__.py              Public exports
│   ├── dtmf.py                  Synthesis, WAV export, playback (backend)
│   └── gui/                     PyQt6 desktop interface (subpackage)
│       ├── __init__.py          Exports MainWindow
│       ├── main_window.py       Main window: layout, state, event handling
│       ├── workers.py           QThread workers (non-blocking generate/play)
│       ├── waveform_canvas.py   Matplotlib waveform preview + live playhead
│       └── theme.py             Dark QSS stylesheet
├── tests/
│   └── test_dtmf.py             Unit tests (pytest) for the backend
├── output/                      Generated .wav files (created at runtime)
├── main.py                      CLI entry point
├── run_gui.py                   GUI entry point
└── readme.md
```

| Module                            | Responsibility                                             |
|------------------------------------|--------------------------------------------------------------|
| `dtmf_dialer/dtmf.py`              | Signal synthesis, WAV file I/O, and audio playback (single source of truth used by both CLI and GUI) |
| `main.py`                          | CLI: reads a phone number (arg or prompt), generates, saves, plays |
| `run_gui.py`                       | Launches the PyQt6 `MainWindow`                              |
| `dtmf_dialer/gui/main_window.py`   | Window layout, input validation, history, waveform display   |
| `dtmf_dialer/gui/workers.py`       | Runs backend calls on background `QThread`s so the UI never blocks |
| `dtmf_dialer/gui/waveform_canvas.py` | Embedded Matplotlib plot with a real-time playback playhead |
| `dtmf_dialer/gui/theme.py`         | Dark QSS stylesheet for the application                      |
| `tests/test_dtmf.py`               | Correctness checks for every synthesis/I/O function           |

## Requirements

| Dependency | Purpose                          |
|------------|-----------------------------------|
| Python ≥ 3.9 | Runtime                         |
| NumPy      | Vectorized signal synthesis       |
| SciPy      | WAV file reading/writing          |
| PyQt6      | Desktop GUI                       |
| Matplotlib | Waveform preview embedded in the GUI |
| pytest     | Running the test suite (optional) |
| Windows OS | `winsound` playback (stdlib)      |

## Installation

```bash
pip install numpy scipy pyqt6 matplotlib pytest
```

## Usage

### CLI

```bash
cd WORK_ONE
python main.py 7004191        # dial a specific number
python main.py                # or omit it and get prompted interactively
```

This generates a WAV file for the given digits, saves it to
`output/dial_<digits>.wav`, and plays it back. Non-digit characters in the
input are ignored.

### GUI

```bash
cd WORK_ONE
python run_gui.py
```

`run_gui.py` is the single script that launches the whole application — it
starts a `QApplication` and shows `MainWindow`, which imports the backend
(`dtmf_dialer.dtmf`) directly. There is no separate server process; the GUI
and backend run in one process, with backend calls offloaded to background
`QThread`s so the interface stays responsive.

In the window:
1. Type a phone number into the input field (digits only — the field
   rejects anything else). The number is never pre-filled or hardcoded.
2. Click **Generate** to synthesize the tones and preview the waveform.
3. Click **Play** to hear it — a green playhead line sweeps across the
   waveform in real time, synced to playback progress.
4. Past dials are kept in a history list; double-clicking one reloads its
   waveform and replays it.

### Programmatic use

```python
from dtmf_dialer import generate_dtmf_sequence, save_wav, play_wav

samples = generate_dtmf_sequence("7004191")
save_wav(samples, "output/dial_7004191.wav")
play_wav("output/dial_7004191.wav")
```

## API Reference

### `generate_tone(low_freq_hz, high_freq_hz, duration_s, sample_rate) -> np.ndarray`
Synthesizes a single DTMF tone as the average of its two component sine
waves, scaled to 16-bit PCM range.

### `generate_silence(duration_s, sample_rate) -> np.ndarray`
Generates a block of zero-valued samples used to separate consecutive tones.

### `generate_dtmf_sequence(digits, tone_duration_s=0.5, pause_duration_s=0.05, sample_rate=44100) -> np.ndarray`
Synthesizes a full dial sequence for a string of digits, concatenating a
tone + pause per valid digit. Characters outside `0`–`9` are skipped.

### `save_wav(samples, path, sample_rate=44100) -> None`
Writes mono 16-bit PCM samples to a `.wav` file.

### `play_wav(path) -> None`
Plays a `.wav` file synchronously via Windows audio (`winsound`).

### `DTMF_FREQUENCIES: dict[str, tuple[int, int]]`
The standard digit → `(low_freq_hz, high_freq_hz)` lookup table.

## DTMF Frequency Table

|       | **1209 Hz** | **1336 Hz** | **1477 Hz** |
|-------|:-----------:|:-----------:|:-----------:|
| **697 Hz** | 1 | 2 | 3 |
| **770 Hz** | 4 | 5 | 6 |
| **852 Hz** | 7 | 8 | 9 |
| **941 Hz** | — | 0 | — |

Only digits `0`–`9` are implemented; `*`, `#`, and the row-4 `A`–`D` tones
(used in military/signaling applications) are outside this package's scope.

## Signal Processing Notes

- **Mixing**: the two sinusoids are averaged (`0.5 × (sin₁ + sin₂)`), not
  summed outright, to keep the combined signal within `[-1, 1]` before
  scaling — this prevents clipping.
- **Quantization**: the normalized signal is scaled to 16-bit PCM range and
  cast to `int16` (NumPy vectorized), following standard digital audio
  quantization practice.
- **Sampling rate**: defaults to 44.1 kHz (CD-quality), comfortably above
  the Nyquist rate needed for the highest DTMF component (1477 Hz).
- **Vectorization**: all synthesis uses NumPy array operations rather than
  per-sample Python loops — standard practice for DSP code, and orders of
  magnitude faster for longer sequences.
- **Waveform preview**: the GUI downsamples long sequences to a fixed
  number of points using a min/max-style envelope (keeps each chunk's
  peak-magnitude sample) so multi-second dial sequences still render a
  responsive, visually faithful plot.
- **Real-time playhead**: `winsound` offers no pollable playback-position
  API, so the GUI tracks elapsed wall-clock time since playback started
  (via a `QTimer` firing every ~33 ms) and maps it onto the waveform's time
  axis — accurate to well within animation-frame granularity.

## Testing

```bash
python -m pytest tests/test_dtmf.py -v
```

15 tests validate:
- Frequency table completeness and correctness (ITU-T Q.23 values)
- Tone sample count, dtype, and amplitude bounds
- Silence generation
- Multi-digit sequence length scaling and invalid-character skipping
- WAV write/read round-trip integrity

`play_wav` is intentionally excluded from automated testing since it
triggers real audio playback.

## Platform Notes

Playback depends on `winsound`, part of the Python standard library on
**Windows only**. Synthesis, WAV export, and tests (`generate_tone`,
`generate_dtmf_sequence`, `save_wav`, etc.) are platform-independent and run
anywhere NumPy/SciPy are available. The GUI (PyQt6 + Matplotlib) also runs
cross-platform, but the **Play** action itself is Windows-only due to the
`winsound` dependency.
