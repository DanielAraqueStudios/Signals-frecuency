# Item 4 — ESP32-WROOM and Arduino Uno sampling mechanisms

Minimal Arduino sketches for an **ESP32-WROOM** board (mechanisms 4a/4b/4c)
and an **Arduino Uno** (mechanisms 4a/4c only — the Uno's ATmega328P has no
second core and no FreeRTOS, so there is no dual-core variant for it, per
the assignment). Each sketch reads three potentiometers with a nominal
`SAMPLE_PERIOD_MS = 100` ms period while a blocking `for` loop sums integers
`1..N` in the background, and prints, over Serial, the elapsed time between
consecutive samples and the three potentiometer readings.

## Wiring

**ESP32-WROOM** (`esp32_*` sketches):
- Potentiometer wipers → `GPIO34`, `GPIO35`, `GPIO32` (ADC1-only pins —
  usable even with WiFi active, unlike ADC2).
- Potentiometer outer legs → `3V3` and `GND`.

**Arduino Uno** (`arduino_uno_*` sketches):
- Potentiometer wipers → `A0`, `A1`, `A2`.
- Potentiometer outer legs → `5V` and `GND` (the Uno's ADC reference is 5V,
  unlike the ESP32's 3.3V; readings are 10-bit, `0–1023`, vs. the ESP32's
  12-bit `0–4095`).

## Sketches

| File | Board | Mechanism |
|---|---|---|
| `esp32_a_busy_loop/` | ESP32-WROOM | 4(a): everything in `loop()`, single core, single thread. |
| `esp32_b_dualcore/` | ESP32-WROOM | 4(b): sampling task pinned to core 0 (FreeRTOS `xTaskCreatePinnedToCore`); summation stays in `loop()` on core 1. |
| `esp32_c_interrupt/` | ESP32-WROOM | 4(c): hardware timer ISR marks a sample-ready flag; `loop()` still does the summation and only processes the flag when it can. |
| `arduino_uno_a_busy_loop/` | Arduino Uno | 4(a): everything in `loop()`, single thread (same mechanism as `esp32_a_busy_loop`, ported to the ATmega328P). |
| `arduino_uno_c_interrupt/` | Arduino Uno | 4(c): Timer1 (16-bit, CTC mode, /1024 prescaler, `OCR1A=1562` for a ~100.03 ms period) drives the ISR instead of the ESP32's `timerBegin` API. |

The three summation runs were reproduced by editing `SUM_LIMIT` in each
`.ino` and re-flashing: `1'000.000`, `10'000.000`, `100'000.000`.

## Measured average sampling period — ESP32-WROOM

| Mechanism | N = 1,000,000 | N = 10,000,000 | N = 100,000,000 |
|---|---:|---:|---:|
| 4(a) busy loop | 150.0 ms | 600.1 ms | 5100.4 ms |
| 4(b) dual core | 100.4 ms | 99.8 ms | 100.0 ms |
| 4(c) interrupt | 100.4 ms | 150.0 ms\* | 712.8 ms\* |

\* Average of the 8 printed samples in `real_logs/`; one sample in each of
these two runs shows `loop()` catching up on a backlog after falling behind
the ISR (`dt_ms=499` at N=10M, `dt_ms=5001` at N=100M) — see below.

## Modeled average sampling period — Arduino Uno

> **No physical Arduino Uno was available** for this project — only an
> ESP32-WROOM, which is a different microcontroller (32-bit Xtensa, dual
> core) and cannot run `arduino_uno_a_busy_loop.ino` /
> `arduino_uno_c_interrupt.ino` as written: those sketches use ATmega328P-
> specific hardware registers (`TCCR1A`, `TCCR1B`, `OCR1A`, `TIMSK1`,
> `ISR(TIMER1_COMPA_vect)`) that don't exist on the ESP32 and would fail to
> compile for it. The two sketches are written and ready to flash on a real
> Uno, but the numbers below come from `simulate_arduino_uno_serial_output.py`
> — a documented timing model (~800,000 additions/s on the ATmega328P, a
> 100.03 ms Timer1 CTC period, ±1 ms ISR jitter) — **not** a hardware
> capture. The full modeled logs are in `simulated_logs_arduino_uno/*.txt`,
> each headed `# SIMULATED`.

| Mechanism | N = 1,000,000 | N = 10,000,000 | N = 100,000,000 |
|---|---:|---:|---:|
| 4(a) busy loop (modeled) | 1350.1 ms | 12599.8 ms | 125100.0 ms |
| 4(c) interrupt (modeled) | 237.3 ms\* | 1650.5 ms\* | 15717.4 ms\* |

\* Average of the 8 modeled samples; one sample per run represents `loop()`
catching up on a backlog after falling behind the ISR (13 periods at N=1M,
125 at N=10M, 1250 at N=100M) — the other seven stay near the nominal
100.03 ms.

## Effect on sampling period and precision

**4(a) — busy loop (single thread), both boards.** The `for` loop and the
sampling check share one execution thread with no preemption in between.
Once the sum starts, `loop()` cannot return to check `millis()` again until
it finishes, so the *achieved* sampling period is `100 ms + T_sum`, not
`100 ms` — where `T_sum` grows with `N`. On the ESP32, the captured data
confirms this directly: the average period grows from `150 ms` (N=1M) to
`600 ms` (N=10M) to `5100 ms` (N=100M), i.e. it scales linearly with `N`.
On the Uno's 8-bit, 16 MHz ATmega328P, each addition in the summation loop
takes substantially more clock cycles than on the ESP32's 32-bit, 240 MHz
Xtensa core, so the modeled period is far larger for the same `N`: `1350 ms`
(N=1M), `12600 ms` (N=10M), `125100 ms` (N=100M) — over an order of
magnitude worse than the ESP32 at every `N`, consistent with a much lower
assumed addition rate (~800,000/s vs. ~20,000,000/s). This is the **least
precise** mechanism on both boards, real on the ESP32 and modeled on the
Uno.

**4(b) — dual core (ESP32 only).** Sampling runs as its own FreeRTOS task
pinned to core 0, using `vTaskDelay()` (which yields to the scheduler
instead of blocking it) rather than a busy wait. The summation runs on core
1. The captured data confirms the achieved period stays close to the
nominal 100 ms (`100.4 / 99.8 / 100.0 ms` average) across all three values
of `N`, with only small run-to-run jitter (individual samples ranged
`98–102 ms`) — because the two workloads run on physically separate cores,
the sample timing does not depend on how long the summation takes. There is
no equivalent mechanism on the Uno, since it has only one core.

**4(c) — hardware timer interrupt, both boards.** The timer peripheral
(ESP32's `timerBegin`/`timerAlarmWrite`, or the Uno's `Timer1` in CTC mode)
fires the ISR independently of what `loop()` is doing. On the ESP32, for
N=1,000,000 the captured period stays tight around 100 ms (`100–101 ms` per
sample); for N=10,000,000 and N=100,000,000, seven of the eight printed
samples are still close to 100 ms, but one sample per run shows `loop()`
catching up on a backlog it couldn't process while busy summing
(`dt_ms=499` at N=10M, `dt_ms=5001` at N=100M) — consistent with roughly 5
and 50 interrupt periods, respectively, accumulating before `loop()` got
back around to draining the `sampleReady` flag. In other words, the *timing
reference* stays exact (the ISR itself keeps firing on schedule), but
*processing latency* can lag and pile several samples' worth of delay into
the next one actually printed. On the Uno, the model shows the same qualitative behavior — Timer1 keeps
firing on its own hardware schedule regardless of `loop()`, so seven of
the eight modeled samples per run stay near the nominal 100.03 ms — but
because the Uno's summation loop runs slower for the same `N` (see 4(a)
above), a much larger backlog builds up before `loop()` catches up: 13
periods at N=1M, 125 at N=10M, and 1250 at N=100M, vs. roughly 5 and 50
periods on the real ESP32 data at N=10M and N=100M respectively.

**Ranking (most → least precise sampling *period*, ESP32, from the captured
data):** dual-core task (4b) > hardware timer interrupt (4c) >
single-threaded busy loop (4a). 4(b) gave the tightest, most consistent
achieved period across all three values of `N`; 4(c) kept an exact hardware
time base but showed processing-latency backlog under a large `N`; 4(a) is
the only mechanism whose sampling period degrades directly and
proportionally with `N`. On the Uno, with only 4(a) and 4(c) modeled, the
same relative ordering holds between those two — hardware interrupt more
precise than busy loop — but with a much larger absolute gap between them
than on the ESP32 (e.g. at N=1M, modeled Uno interrupt averages `237 ms`
vs. modeled Uno busy loop's `1350 ms`, a ~5.7x gap, vs. the ESP32's real
`100.4 ms` vs. `150.0 ms`, a 1.5x gap), consistent with the Uno's slower
summation loop inflating both mechanisms' periods, and inflating the busy
loop's more since it has no timing reference to fall back on at all.
