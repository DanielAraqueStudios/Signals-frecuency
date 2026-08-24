/*
 * Item 4(a) - ESP32-WROOM, single-threaded busy loop.
 *
 * Every SAMPLE_PERIOD_MS, read 3 potentiometers on ADC1 channels and print
 * the time elapsed since the previous sample. Right after sampling, block
 * the loop by summing 1..N (N is swapped between runs to see its effect on
 * the achieved sampling period): the summation and the sampling share the
 * same single thread, so a large N delays the next sample directly.
 *
 * Wiring: potentiometer wipers -> GPIO34, GPIO35, GPIO32 (ADC1-only pins,
 * safe to use with WiFi active). Outer legs -> 3V3 and GND.
 */

const int POT_PINS[3] = {34, 35, 32};
const unsigned long SAMPLE_PERIOD_MS = 100;

// Swap this between runs: 10000000UL, 1000000UL, 100000000UL
const unsigned long SUM_LIMIT = 10000000UL;

unsigned long lastSampleMs = 0;

void setup() {
  Serial.begin(115200);
  analogReadResolution(12); // 0-4095
  lastSampleMs = millis();
}

void loop() {
  unsigned long now = millis();
  if (now - lastSampleMs >= SAMPLE_PERIOD_MS) {
    unsigned long dt = now - lastSampleMs;
    lastSampleMs = now;

    int a = analogRead(POT_PINS[0]);
    int b = analogRead(POT_PINS[1]);
    int c = analogRead(POT_PINS[2]);

    Serial.printf("dt_ms=%lu pot1=%d pot2=%d pot3=%d\n", dt, a, b, c);
  }

  // Blocking workload: this is what starves the sampling check above when
  // SUM_LIMIT is large, since loop() cannot return to check millis() again
  // until the sum finishes.
  volatile unsigned long long sum = 0;
  for (unsigned long i = 0; i < SUM_LIMIT; i++) {
    sum += i;
  }
}
