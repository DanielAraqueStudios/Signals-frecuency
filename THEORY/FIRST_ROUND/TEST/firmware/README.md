# Item 4 — ESP32-WROOM sampling mechanisms

Three minimal Arduino sketches for an **ESP32-WROOM** board, each reading
three potentiometers with a nominal `SAMPLE_PERIOD_MS = 100` ms period while
a blocking `for` loop sums integers `1..N` in the background. Each sketch
prints, over Serial, the elapsed time between consecutive samples and the
three potentiometer readings. Raw captures from the Arduino IDE Serial
Monitor (115200 baud) for all three sketches, at all three assignment
`SUM_LIMIT` values, are in `real_logs/`.

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

The three summation runs were reproduced by editing `SUM_LIMIT` in each
`.ino` and re-flashing: `1'000.000`, `10'000.000`, `100'000.000`.

## Measured average sampling period

| Mechanism | N = 1,000,000 | N = 10,000,000 | N = 100,000,000 |
|---|---:|---:|---:|
| 4(a) busy loop | 150.0 ms | 600.1 ms | 5100.4 ms |
| 4(b) dual core | 100.4 ms | 99.8 ms | 100.0 ms |
| 4(c) interrupt | 100.4 ms | 150.0 ms\* | 712.8 ms\* |

\* Average of the 8 printed samples in `real_logs/`; one sample in each of
these two runs shows `loop()` catching up on a backlog after falling behind
the ISR (`dt_ms=499` at N=10M, `dt_ms=5001` at N=100M) — see below.

## Effect on sampling period and precision

**4(a) — busy loop (single thread).** The `for` loop and the sampling check
share one execution thread with no preemption in between. Once the sum
starts, `loop()` cannot return to check `millis()` again until it finishes,
so the *achieved* sampling period is `100 ms + T_sum`, not `100 ms` — where
`T_sum` grows with `N`. The captured data confirms this directly: the
average period grows from `150 ms` (N=1M) to `600 ms` (N=10M) to `5100 ms`
(N=100M), i.e. it scales linearly with `N` and the nominal 100 ms period is
effectively lost for large `N`. This is the **least precise** mechanism.

**4(b) — dual core.** Sampling runs as its own FreeRTOS task pinned to core
0, using `vTaskDelay()` (which yields to the scheduler instead of blocking
it) rather than a busy wait. The summation runs on core 1. The captured data
confirms the achieved period stays close to the nominal 100 ms
(`100.4 / 99.8 / 100.0 ms` average) across all three values of `N`, with
only small run-to-run jitter (individual samples ranged `98–102 ms`) —
because the two workloads run on physically separate cores, the sample
timing does not depend on how long the summation takes.

**4(c) — hardware timer interrupt.** The ESP32's hardware timer peripheral
fires the ISR independently of what `loop()` is doing. For N=1,000,000 the
captured period stays tight around 100 ms (`100–101 ms` per sample). For
N=10,000,000 and N=100,000,000, seven of the eight printed samples are still
close to 100 ms, but one sample per run shows `loop()` catching up on a
backlog it couldn't process while busy summing (`dt_ms=499` at N=10M,
`dt_ms=5001` at N=100M) — consistent with roughly 5 and 50 interrupt periods,
respectively, accumulating before `loop()` got back around to draining the
`sampleReady` flag. In other words, the *timing reference* stays exact
(the ISR itself keeps firing on schedule), but *processing latency* can lag
and pile several samples' worth of delay into the next one actually printed.

**Ranking (most → least precise sampling *period*, from the captured data):**
dual-core task (4b) > hardware timer interrupt (4c) > single-threaded busy
loop (4a). 4(b) gave the tightest, most consistent achieved period across
all three values of `N`; 4(c) kept an exact hardware time base but showed
processing-latency backlog under a large `N`; 4(a) is the only mechanism
whose sampling period degrades directly and proportionally with `N`.
