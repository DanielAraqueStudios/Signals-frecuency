# Item 4 — ESP32-WROOM sampling mechanisms

Three minimal Arduino sketches for an **ESP32-WROOM** board, each reading
three potentiometers with a nominal `SAMPLE_PERIOD_MS = 100` ms period while
a blocking `for` loop sums integers `1..N` in the background. Each sketch
prints, over Serial, the elapsed time between consecutive samples and the
three potentiometer readings.

> **Not executed on real hardware.** No ESP32/Arduino was available in this
> environment to flash and measure. The code below is written to compile and
> run as-is on an ESP32-WROOM dev board; the timing discussion is a
> theoretical analysis based on how each mechanism actually behaves, not
> measured serial output.

## Wiring (all three sketches)

- Potentiometer wipers → `GPIO34`, `GPIO35`, `GPIO32` (ADC1-only pins —
  usable even with WiFi active, unlike ADC2).
- Potentiometer outer legs → `3V3` and `GND`.

## Sketches

| File | Mechanism |
|---|---|
| `esp32_a_busy_loop/` | 4(a): everything in `loop()`, single core, single thread. |
| `esp32_b_dualcore/` | 4(b): sampling task pinned to core 0 (FreeRTOS `xTaskCreatePinnedToCore`); summation stays in `loop()` on core 1. |
| `esp32_c_interrupt/` | 4(c): hardware timer ISR marks a sample-ready flag; `loop()` still does the summation and only processes the flag when it can. |

To reproduce the assignment's three summation runs, edit `SUM_LIMIT` (or
`SUM_LIMIT` in the dual-core case) in each `.ino` before re-flashing:
`10'000.000`, `1'000.000`, `100'000.000`.

## Expected effect on sampling period and precision

**4(a) — busy loop (single thread).** The `for` loop and the sampling check
share one execution thread with no preemption in between. Once the sum
starts, `loop()` cannot return to check `millis()` again until it finishes,
so the *achieved* sampling period is `100 ms + T_sum`, not `100 ms` — where
`T_sum` grows with `N`. At `N = 10'000.000` this adds a small, roughly
constant delay per cycle; at `N = 100'000.000` the delay dominates and the
real period could stretch to seconds, i.e. the requested 100 ms period is
effectively lost. This is the **least precise** mechanism, and it degrades
predictably as `N` grows.

**4(b) — dual core.** Sampling runs as its own FreeRTOS task pinned to core
0, using `vTaskDelay()` (which yields to the scheduler instead of blocking
it) rather than a busy wait. The summation runs on core 1. Because the two
workloads run on physically separate cores, the sample timing does not
depend on how long the summation takes — the achieved period should stay
close to the requested 100 ms regardless of `N`, only picking up jitter from
FreeRTOS scheduling overhead and any other core-0 activity (WiFi/BT stack
callbacks also run on core 0 by default on many ESP32 configurations, which
is the main source of residual jitter). This is markedly **more precise**
than 4(a) for large `N`.

**4(c) — hardware timer interrupt.** The ESP32's hardware timer peripheral
fires the ISR independently of what `loop()` is doing; `lastIsrMs`/`isrDeltaMs`
are captured with hardware-clock accuracy exactly on schedule, even while the
summation is running. What *does* get delayed by a large `N` is not the
sample *timestamp*, but how soon `loop()` gets around to reading the
potentiometers and printing that sample once `sampleReady` is set — so
several interrupt periods can elapse (and their `dt` values pile up) before
`loop()` catches up and drains them one at a time. In other words, the
*timing reference* is exact, but *processing latency* can lag, and if `N` is
large enough for long enough, `sampleReady` events can be produced faster
than `loop()` drains them (this minimal sketch keeps only the latest one,
so intermediate samples between two `loop()` iterations are effectively
merged rather than dropped explicitly).

**Ranking (most → least precise sampling *period*):** hardware timer
interrupt (4c) ≳ dual-core task (4b) ≫ single-threaded busy loop (4a). The
interrupt-driven approach gives the most accurate *time base* (the ISR fires
on hardware-clock schedule no matter what `loop()` is doing); the dual-core
approach gives the most accurate *end-to-end* sampling (reading the ADC and
emitting the line at close to the true 100 ms cadence) since the reads
themselves aren't queued up behind a busy core; the busy loop is the only
one of the three where the summation directly and proportionally corrupts
the achieved sampling period.
