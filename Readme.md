# Signals-frecuency

A personal collection of signal-processing projects. This repository
collects standalone, self-contained projects, each living in its own
top-level folder with its own README, dependencies, and tests.

---

## Tech Stack

| Layer              | Technology                          |
|---------------------|--------------------------------------|
| Language            | Python 3.9+                          |
| Numerical / DSP      | NumPy, SciPy                        |
| Desktop GUI          | PyQt6, Matplotlib (embedded plots)  |
| Testing              | pytest                              |
| Audio I/O            | `winsound` (stdlib, Windows)        |
| Tooling              | Git, claude-flow (dev-agent tooling; not part of the shipped projects) |

## Repository Structure

```
Signals-frecuency/
├── WORK_ONE/          DTMF Dialer — signal synthesis + CLI + desktop GUI
├── Readme.md          This file — repository index
└── .gitignore
```

Each project folder is independent: it has its own README with setup,
usage, and API details. This root README is only an index — see the
[Projects](#projects) section below for a one-line description and link to
each one.

## Projects

### [`WORK_ONE/` — DTMF Dialer](WORK_ONE/readme.md)

A Python package that synthesizes, exports, and plays **DTMF
(Dual-Tone Multi-Frequency)** dial tones — the audio signal a telephone
keypad produces when a digit is pressed — using vectorized NumPy sine-wave
synthesis per the ITU-T Q.23 standard. Ships with a CLI, a full PyQt6
desktop GUI (threaded backend calls, dark theme, real-time waveform
playhead), and a pytest unit test suite.

**Stack:** NumPy · SciPy · PyQt6 · Matplotlib · pytest
**Entry points:** `python main.py <number>` (CLI) · `python run_gui.py` (GUI)
**Full docs:** [`WORK_ONE/readme.md`](WORK_ONE/readme.md)

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
cd WORK_ONE
pip install numpy scipy pyqt6 matplotlib pytest
python main.py 7004191      # CLI
python run_gui.py           # GUI
```

## About

A personal project exploring signal-processing concepts. Each folder is a
self-contained exercise built independently.
