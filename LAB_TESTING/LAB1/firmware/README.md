# LAB1 firmware — STM32 (32-bit) signal digitization/reconstruction

Five sketches, one per stage of the practice, written for an STM32
Nucleo-64 board via the STM32duino (`Arduino_Core_STM32`) core. **No
physical STM32 board, oscilloscope, wave generator, IMU, or encoder/motor
was available in this environment** — these sketches are written to
compile and run as-is, but have not been flashed or tested on real
hardware. `report/` treats every hardware-dependent result as pending real
capture rather than fabricating oscilloscope/sensor readings.

## Sketches

| Folder | Stage | Sample rate | Notes |
|---|---|---|---|
| `part1_digitization/` | Digitalización de señales periódicas | 500 Hz (2 ms) | Toggles a debug pin each tick + 12-bit ADC capture. |
| `part2_dac_reconstruction/` | Reconstrucción — DAC | 500 Hz (2 ms) | ADC capture immediately mirrored to the onboard DAC. |
| `part2_pwm_reconstruction/` | Reconstrucción — PWM + filtro | 500 Hz (2 ms) capture, 5 kHz PWM | Duty cycle mapped 1–99% from the ADC code; needs an external active low-pass filter (not firmware — see report). |
| `part3_imu_sensor/` | Digitalización de sensores — IMU | 200 Hz (5 ms) | 6-channel I2C IMU (MPU-6050 register map assumed; adjust per actual sensor). |
| `part3_encoder_motor/` | Digitalización de sensores — encoder | 200 Hz (5 ms) | Pulse-counting strategy; `PULSES_PER_REV` must be set from the real encoder. |

## Binary framing and baud rate

All frames start with a distinct sync byte so `pc_logger/serial_logger.py`
can resynchronize after any dropped byte, and carry raw ADC/sensor codes —
unit conversion happens PC-side, keeping every ISR short.

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

- **Part 1**: ADC input `PA0` ← wave generator (30–125 Hz sinusoid) or a
  potentiometer for preliminary tests; debug pin `PA5` → oscilloscope, to
  verify the 2 ms interrupt period.
- **Part 2 (DAC)**: ADC `PA0` ← generator; DAC `PA4` → oscilloscope
  channel 2, compared against the generator on channel 1.
- **Part 2 (PWM)**: ADC `PA0` ← generator; PWM `PB10` → external active
  low-pass filter → oscilloscope channel 2. The filter itself (0 dB gain
  at 500 Hz, ≤ −20 dB by 600 Hz) is analog hardware outside this firmware;
  a 2nd-order Sallen-Key low-pass is suggested in the report, since a
  single RC stage's −20 dB/decade roll-off cannot reach −20 dB only
  100 Hz above a 500 Hz cutoff.
- **Part 3 (IMU)**: I2C `SDA`→`PB7`, `SCL`→`PB6`, `VCC`→`3V3`, `GND`→`GND`.
- **Part 3 (encoder/motor)**: encoder channel A → `PA1` (interrupt pin),
  channel B → `PA2` (direction sign); motor driver per the driver module's
  own datasheet.

## Adjusting for a different board

Every pin name (`PA0`, `PA4`, `PB10`, …) is a Nucleo-64 Arduino-style
alias. If a different STM32 board/package is used, remap these to that
board's actual ADC-, DAC-, PWM-, and timer-capable pins before flashing.
