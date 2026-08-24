# Signals-frecuency

A personal collection of signal-processing projects. This repository
collects standalone, self-contained projects, each living in its own
folder with its own README, dependencies, and tests, grouped under a
`THEORY/` tree by assignment round.

---

## Tech Stack

| Layer              | Technology                          |
|---------------------|--------------------------------------|
| Language            | Python 3.9+                          |
| Numerical / DSP      | NumPy, SciPy                        |
| Desktop GUI          | PyQt6, customtkinter, Matplotlib (embedded plots) |
| Testing              | pytest                              |
| Audio I/O            | `winsound` (stdlib, Windows), librosa/soundfile, scipy.io.wavfile |
| Embedded             | ESP32-WROOM / Arduino Uno (C++, FreeRTOS) |
| Reporting            | LaTeX (IEEEtran) |
| Tooling              | Git, claude-flow (dev-agent tooling; not part of the shipped projects) |

## Repository Structure

```
Signals-frecuency/
├── THEORY/
│   └── FIRST_ROUND/
│       ├── WORK/
│       │   ├── WORK_ONE/      DTMF Dialer — signal synthesis + CLI + desktop GUI
│       │   ├── WORK_TWO/      Fourier Square-Wave Sampling — series synthesis + visualization
│       │   └── WORK_THREE/    Sampling & Spectral Analysis Lab — sine/square/triangular sampling, FFT, audio stats
│       └── TEST/              Sampling, Quantization, Audio FFT & Embedded Timing — CSV/audio analysis + ESP32 firmware
├── LAB_TESTING/                Reserved for upcoming lab work (currently empty)
├── Readme.md                   This file — repository index
└── .gitignore
```

Each project folder is independent: it has its own README with setup,
usage, and API details. This root README is only an index — see the
[Projects](#projects) section below for a one-line description and link to
each one.

## Projects

### [`THEORY/FIRST_ROUND/WORK/WORK_ONE/` — DTMF Dialer](THEORY/FIRST_ROUND/WORK/WORK_ONE/readme.md)

A Python package that synthesizes, exports, and plays **DTMF
(Dual-Tone Multi-Frequency)** dial tones — the audio signal a telephone
keypad produces when a digit is pressed — using vectorized NumPy sine-wave
synthesis per the ITU-T Q.23 standard. Ships with a CLI, a full PyQt6
desktop GUI (threaded backend calls, dark theme, real-time waveform
playhead), and a pytest unit test suite.

**Stack:** NumPy · SciPy · PyQt6 · Matplotlib · pytest
**Entry points:** `python main.py <number>` (CLI) · `python run_gui.py` (GUI)
**Full docs:** [`readme.md`](THEORY/FIRST_ROUND/WORK/WORK_ONE/readme.md)

### [`THEORY/FIRST_ROUND/WORK/WORK_TWO/` — Fourier Square-Wave Sampling](THEORY/FIRST_ROUND/WORK/WORK_TWO/readme.md)

A Python package that reconstructs a **square wave from its Fourier sine
series** (odd harmonics, ITU-style vectorized NumPy synthesis) and
visualizes the result across several sampling rates — illustrating Gibbs
phenomenon and how sample density relates to the sampling theorem. Ships
with a small testable package (synthesis + plotting split apart) and a
pytest unit test suite.

**Stack:** NumPy · Matplotlib · pytest
**Entry point:** `python main.py`
**Full docs:** [`readme.md`](THEORY/FIRST_ROUND/WORK/WORK_TWO/readme.md)

### [`THEORY/FIRST_ROUND/WORK/WORK_THREE/` — Sampling & Spectral Analysis Lab](THEORY/FIRST_ROUND/WORK/WORK_THREE/readme.md)

A Python package covering sine/triangular/Fourier-series-square-wave
**sampling** exercises across several sampling rates, an **ideal-vs-truncated**
FFT comparison, and a customtkinter **desktop GUI** that runs mean/std/FFT
statistics on animal, instrument, and voice recordings to study how
statistically separable they are. Includes a modular IEEE-conference
**LaTeX report** (`report/main.tex`) built from real audio (animals and
instruments sourced from Wikimedia Commons, voices synthesized locally),
with every figure and result table generated from the actual pipeline.

**Stack:** NumPy · SciPy · Matplotlib · customtkinter · librosa · pytest · LaTeX
**Entry points:** `python main.py` (sampling/Fourier demo) · `python run_animal_gui.py` (GUI) · `report/main.tex` (report)
**Full docs:** [`readme.md`](THEORY/FIRST_ROUND/WORK/WORK_THREE/readme.md)

### [`THEORY/FIRST_ROUND/TEST/` — Sampling, Quantization, Audio FFT & Embedded Timing](THEORY/FIRST_ROUND/TEST/readme.md)

A Python package covering four exercises: loading and segmenting a recorded
CSV signal, **sampling + DAC-style quantization** of a 100 Hz sine to
illustrate aliasing, an **FFT comparison** of three real audio sources
(violin, drum, cat), and minimal **ESP32-WROOM firmware** comparing three
concurrency mechanisms (busy loop, dual-core, hardware-timer interrupt) for
periodic analog sampling under a variable compute load. Includes a modular
IEEE-conference **LaTeX report** (`report/main.tex`) built from the real CSV
and audio data; the embedded-timing section is explicitly labeled as a
documented simulation, since no physical ESP32/Arduino hardware was
available to flash and measure.

**Stack:** NumPy · SciPy · Matplotlib · pytest · LaTeX · Arduino/ESP32 (C++)
**Entry points:** `python main.py` (items 1-3) · `firmware/` (item 4 sketches + simulated logs) · `report/main.tex` (report)
**Full docs:** [`readme.md`](THEORY/FIRST_ROUND/TEST/readme.md)

> More projects will be added here as new exercises are completed, each
> following the same pattern: its own folder, its own README, linked above.

## Getting Started

```bash
git clone <this-repo-url>
cd Signals-frecuency
```

Then open the project folder you're interested in and follow its README —
for example:

```bash
cd THEORY/FIRST_ROUND/WORK/WORK_ONE
pip install numpy scipy pyqt6 matplotlib pytest
python main.py 7004191      # CLI
python run_gui.py           # GUI
```

## About

A personal project exploring signal-processing concepts. Each folder is a
self-contained exercise built independently.
