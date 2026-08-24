# LAB1 firmware — ESP32-WROOM signal digitization/reconstruction

Five sketches, one per stage of the practice, written for an **ESP32-WROOM**
board via the Arduino core for ESP32. The lab guide names an STM32 board
specifically for the PWM reconstruction stage; this project targets ESP32
hardware throughout instead, since that's the board actually available.
**No physical ESP32 board, oscilloscope, wave generator, IMU, or
encoder/motor was available in this environment** — these sketches are
written to compile and run as-is, but have not been flashed or tested on
real hardware. `report/` treats every hardware-dependent result as pending
real capture rather than fabricating oscilloscope/sensor readings.

## Important hardware difference vs. the STM32 the guide names

The ESP32's built-in DAC (`part2_dac_reconstruction/`) is only **8-bit**
(GPIO25/26, values 0–255), not 12-bit like an STM32's. The ADC still
captures at the required 12-bit resolution (0–4095); the 12-bit code is
scaled down (`code >> 4`) only for the DAC write. This means the
DAC-reconstructed waveform has coarser amplitude resolution than the
capture itself — a genuine ESP32 hardware limitation, not a firmware
choice, worth calling out explicitly when comparing the DAC and PWM
reconstruction methods (Section on reconstruction, `report/secciones/`).

The ESP32's ADC is also known to be less linear than an ideal 12-bit
converter, particularly near the rails — worth keeping in mind when
comparing captured voltages against the generator's configured amplitude.

## Sketches

| Folder | Stage | Sample rate | Notes |
|---|---|---|---|
| `part1_digitization/` | Digitalización de señales periódicas | 500 Hz (2 ms) | Hardware timer ISR toggles a debug pin + captures the ADC; Serial send happens in `loop()` (not the ISR — see below). |
| `part2_dac_reconstruction/` | Reconstrucción — DAC | 500 Hz (2 ms) | ADC capture mirrored to the 8-bit DAC, same ISR. |
| `part2_pwm_reconstruction/` | Reconstrucción — PWM + filtro | 500 Hz (2 ms) capture, 5 kHz PWM (LEDC, 10-bit duty) | Duty mapped 1–99% from the ADC code; needs an external active low-pass filter (not firmware — see report). |
| `part3_imu_sensor/` | Digitalización de sensores — IMU | 200 Hz (5 ms) | 6-channel I2C IMU (MPU-6050 register map assumed; adjust per actual sensor). |
| `part3_encoder_motor/` | Digitalización de sensores — encoder | 200 Hz (5 ms) | Pulse-counting strategy; `PULSES_PER_REV` must be set from the real encoder. |

## Why Serial I/O happens in `loop()`, not the ISR

`Serial.write()` is not guaranteed interrupt-safe on the ESP32's Arduino
core (the UART driver can be interrupted mid-transaction by other code).
Every sketch here follows the same safe pattern: the hardware-timer ISR
only does the minimum needed work (toggle a pin, read the ADC/encoder
counter, write the DAC/PWM register) inside a short critical section, sets
a `sampleReady` flag, and `loop()` — running continuously with nothing else
to do — checks that flag and performs the actual `Serial.write()`. This
adds a small, bounded latency between capture and transmission (at most one
`loop()` iteration, which on an otherwise-empty loop is on the order of
microseconds) without risking a corrupted or hung UART transaction.

`analogRead()` inside the ISR (used in `part1`/`part2` for the ADC capture)
is common practice in ESP32 Arduino sketches but is not officially
documented as interrupt-safe either — this is a known risk worth verifying
directly against a real board (e.g. confirming no watchdog resets or
missed samples occur) once hardware is available, per the assignment's own
requirement to verify the interrupt period on the oscilloscope.

## Binary framing and baud rate

Unchanged from the original STM32 design — all frames start with a
distinct sync byte so `pc_logger/serial_logger.py` can resynchronize after
any dropped byte, and carry raw ADC/sensor codes; unit conversion happens
PC-side.

| Sketch | Frame size | Rate | Required throughput |
|---|---:|---:|---:|
| `part1_digitization` | 3 B | 500 Hz | 1,500 B/s |
| `part2_*_reconstruction` | 3 B | 500 Hz | 1,500 B/s |
| `part3_imu_sensor` | 14 B | 200 Hz | 2,800 B/s |
| `part3_encoder_motor` | 5 B | 200 Hz | 1,000 B/s |

At 9,600 baud (≈960 B/s usable after start/stop bits), none of these fit —
the assignment's warning that 9,600 bit/s is insufficient checks out
numerically once framing overhead is counted. `part1`/`part2` use 115,200
baud (≈11,520 B/s, a 7.7x margin over 1,500 B/s); `part3_imu_sensor` uses
230,400 baud (≈23,040 B/s, an 8.2x margin over 2,800 B/s) since it carries
the most bytes/sample of the five sketches.

## Wiring summary

- **Part 1**: ADC input `GPIO34` (ADC1-only, usable even with WiFi active)
  ← wave generator (30–125 Hz sinusoid) or a potentiometer for preliminary
  tests; debug pin `GPIO5` → oscilloscope, to verify the 2 ms interrupt
  period.
- **Part 2 (DAC)**: ADC `GPIO34` ← generator; DAC `GPIO25` (one of the
  ESP32's two true DAC pins, 8-bit) → oscilloscope channel 2, compared
  against the generator on channel 1.
- **Part 2 (PWM)**: ADC `GPIO34` ← generator; PWM `GPIO26` (LEDC channel 0)
  → external active low-pass filter → oscilloscope channel 2. The filter
  itself (0 dB gain at 500 Hz, ≤ −20 dB by 600 Hz) is analog hardware
  outside this firmware; a 2nd-order Sallen-Key low-pass is suggested in
  the report, since a single RC stage's −20 dB/decade roll-off cannot
  reach −20 dB only 100 Hz above a 500 Hz cutoff.
- **Part 3 (IMU)**: I2C `SDA`→`GPIO21`, `SCL`→`GPIO22` (ESP32
  `Wire.begin()` defaults), `VCC`→`3V3`, `GND`→`GND`.
- **Part 3 (encoder/motor)**: encoder channel A → `GPIO4` (interrupt pin),
  channel B → `GPIO16` (direction sign); motor driver per the driver
  module's own datasheet.

## If an STM32 is used instead

The original STM32 design (STM32duino `HardwareTimer`, 12-bit
`analogWrite()` DAC, STM32 timer-based PWM) is preserved in this project's
git history (see the commit that introduced the ESP32 port) and can be
restored if the actual hardware changes back to an STM32 board.
