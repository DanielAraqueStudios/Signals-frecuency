# Sampling, Quantization, Audio FFT & Embedded Timing

> Part of the [`Signals-frecuency`](../../../Readme.md) repository — see the root
> README for the full project index.

A Python package covering four exercises: analysis of a recorded signal
(`Muestra01.csv`), sampling + DAC-style quantization of a 100 Hz sine to
illustrate aliasing, an FFT comparison of three real audio sources (violin,
drum, cat), and minimal ESP32-WROOM firmware comparing three concurrency
mechanisms for periodic analog sampling.

---

## Table of Contents

- [Scope](#scope)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Item 4 — Firmware](#item-4--firmware)
- [Testing](#testing)

---

## Scope

| Item | Description | Where |
|------|-------------|-------|
| 1 | Load `Muestra01.csv` (fs=5000 Hz), split into 0.05 s segments, get dominant frequency per segment | `signal_tools.csv_signal`, `main.py` |
| 2 | Sample a 100 Hz sine at 70/500/1000 Hz, quantize with a DAC-style algorithm, explain aliasing | `signal_tools.sampling`, `main.py` |
| 3 | FFT of a violin, drum, and cat recording; discuss frequency-based separability | `signal_tools.audio_fft`, `main.py` |
| 4 | ESP32-WROOM + Arduino Uno: compare busy-loop, dual-core, and interrupt-driven sampling under a variable compute load | `firmware/` |

## Project Structure

```
TEST/
├── signal_tools/                Core package: items 1-3
│   ├── __init__.py               Public exports
│   ├── csv_signal.py             Muestra01.csv loading, segmenting, FFT (item 1)
│   ├── sampling.py               Sine synthesis, sampling, DAC quantization, aliasing check (item 2)
│   ├── audio_fft.py              WAV loading + FFT spectrum (item 3)
│   └── plotting.py               Matplotlib figure assembly, one function per item
├── audio_samples/
│   ├── violin.wav
│   ├── tambor.wav
│   └── gato.wav
├── firmware/                     Item 4: ESP32-WROOM (a/b/c) + Arduino Uno (a/c) sketches
│   ├── esp32_a_busy_loop/
│   ├── esp32_b_dualcore/
│   ├── esp32_c_interrupt/
│   ├── arduino_uno_a_busy_loop/  Uno has no second core -> no 4(b) variant
│   ├── arduino_uno_c_interrupt/  Timer1 CTC-mode ISR instead of ESP32's timerBegin
│   ├── real_logs/                Raw Serial Monitor captures (ESP32 done, Uno pending)
│   └── README.md                 Wiring + measured timing/precision analysis
├── tests/
│   ├── test_csv_signal.py
│   ├── test_sampling.py
│   └── test_audio_fft.py
├── report/                       IEEE-conference LaTeX write-up of items 1-4
│   ├── main.tex
│   ├── secciones/
│   └── figuras/
├── main.py                       Entry point: runs items 1-3, saves report figures
├── Muestra01.csv
├── Parcial punto1.py              Original draft script (superseded by signal_tools + main.py)
├── Parcial punto2.py               "
├── Parcial punto3.py                "
└── readme.md
```

## Requirements

| Dependency | Purpose |
|---|---|
| numpy | FFT, array math |
| scipy | WAV file I/O (`scipy.io.wavfile`) |
| matplotlib | Plotting |
| pytest | Test suite |

```bash
pip install numpy scipy matplotlib pytest
```

## Usage

```bash
cd THEORY/FIRST_ROUND/TEST
python main.py            # run items 1-3, save figures to report/figuras/
python main.py --show     # also open interactive plot windows
```

## API Reference

- `signal_tools.load_csv_signal(path)` / `segment_signal(signal, sample_rate, segment_duration_s)` / `dominant_frequency(segment, sample_rate)`
- `signal_tools.sine_wave(frequency_hz, t, amplitude=1.0)` / `sample_signal(frequency_hz, sample_rate_hz, duration_s)` / `quantize_dac(signal, bits=3)` / `is_aliased(signal_frequency_hz, sample_rate_hz)`
- `signal_tools.load_wav(path)` / `compute_fft_spectrum(signal, sample_rate)`

## Item 4 — Firmware

Per the assignment, the ESP32-WROOM gets all three mechanisms (4a/4b/4c);
the Arduino Uno gets only 4(a) and 4(c), since its ATmega328P has no second
core and no FreeRTOS for a dual-core variant. All three ESP32 sketches were
flashed on a real board and their serial output captured directly with the
Arduino IDE's Serial Monitor (115200 baud) — see `firmware/real_logs/` and
`report/secciones/embebidos.tex`. The two Uno sketches
(`arduino_uno_a_busy_loop/`, `arduino_uno_c_interrupt/`) are written and
ready to flash, but still need a real capture — `firmware/README.md` has
the pending-data note and expected wiring/timing analysis.

## Testing

```bash
python -m pytest tests/ -v
```

23 tests, all passing. `load_wav` (thin I/O over `scipy.io.wavfile`) is
exercised end-to-end via `python main.py` against the real recordings in
`audio_samples/`, rather than unit-tested in isolation.
