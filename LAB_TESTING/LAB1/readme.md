# LAB1 — Digitalización de señales y aliasing

> Part of the [`Signals-frecuency`](../../Readme.md) repository — see the
> root README for the full project index.

A complete signal-digitization system for a 32-bit microcontroller (STM32
Nucleo-64), covering periodic-signal sampling, signal reconstruction (DAC
and PWM + low-pass filter), sensor digitization (IMU + encoder/DC-motor),
and the aliasing phenomenon — matching each stage of the university lab
guide reproduced in `report/secciones/`.

**No physical hardware was available** to build this (STM32 board,
oscilloscope, wave generator, IMU, encoder/motor): the firmware, PC-side
logger, and MATLAB analysis scripts are complete and ready to run, but the
report's result tables are honestly marked *pendiente* (pending) rather
than containing invented measurements. See `report/secciones/resultados.tex`.

---

## Project Structure

```
LAB1/
├── firmware/                        STM32 sketches (STM32duino/Arduino core), one per stage
│   ├── part1_digitization/           500 Hz timer-ISR sampling, 12-bit ADC
│   ├── part2_dac_reconstruction/     Reconstruction via the onboard DAC
│   ├── part2_pwm_reconstruction/     Reconstruction via 5 kHz PWM + external filter
│   ├── part3_imu_sensor/             200 Hz, 6-channel I2C IMU capture
│   ├── part3_encoder_motor/          200 Hz encoder pulse-counting
│   └── README.md                     Wiring, framing, baud-rate justification
├── pc_logger/
│   ├── serial_logger.py              Binary-frame receiver -> CSV (no plotting, per the assignment)
│   └── tests/
│       └── test_serial_logger.py     14 tests against synthetic byte streams
├── matlab/
│   ├── analyze_periodic_signal.m     FFT + normalized-frequency table (Part 1)
│   ├── analyze_imu.m                 Stats + bandwidth per IMU channel (Part 3)
│   ├── analyze_encoder.m             Velocity stats + bandwidth (Part 3)
│   ├── analyze_aliasing.m            Folded-frequency table (optional aliasing section)
│   └── README.md
├── data/                             Empty placeholders for real captures, one per experiment
│   ├── periodic_signal/
│   ├── reconstruction/
│   ├── imu_still/
│   ├── imu_moving/
│   ├── encoder/
│   └── aliasing/
├── report/                           IEEE-conference LaTeX report (en español)
│   ├── main.tex
│   ├── secciones/
│   └── figuras/
└── readme.md
```

## Requirements

| Dependency | Purpose |
|---|---|
| Arduino IDE + STM32duino core | Compile/flash the `firmware/*/*.ino` sketches |
| Python 3.9+, `pyserial` | `pc_logger/serial_logger.py` |
| pytest | `pc_logger/tests/` |
| MATLAB | `matlab/*.m` analysis scripts |

```bash
pip install pyserial pytest
```

## Usage (once hardware is available)

```bash
# 1. Flash the relevant sketch from firmware/ onto the STM32 board.
# 2. Capture data to CSV:
cd pc_logger
python serial_logger.py --mode adc     --port COM5 --baud 115200 --out ../data/periodic_signal/signal_50hz.csv
python serial_logger.py --mode imu     --port COM5 --baud 230400 --out ../data/imu_still/imu_still.csv
python serial_logger.py --mode encoder --port COM5 --baud 115200 --out ../data/encoder/encoder_5v.csv --pulses-per-rev 20

# 3. Analyze in MATLAB:
#    analyze_periodic_signal('../data/periodic_signal/signal_50hz.csv', 500, 50);
```

## Testing

```bash
cd pc_logger
python -m pytest tests/ -v
```

14 tests, all passing — cover the binary-frame decoding math (ADC→volts,
IMU raw→physical units, encoder pulses→angle/velocity) and the
frame-resync parser, using synthetic byte streams rather than a live
serial port.

## Report

`report/main.tex` (IEEEtran, Spanish) covers all four stages of the guide,
including the optional aliasing section. Result tables fill in every value
derivable from pure sampling theory (calculated normalized frequency,
samples/cycle, theoretical aliased frequencies) and mark every
hardware-dependent value as *pendiente*; the reflection/discussion
questions are answered from DSP theory throughout. Once real captures
exist in `data/`, run the corresponding `matlab/*.m` script and replace the
pending cells with the real output.
