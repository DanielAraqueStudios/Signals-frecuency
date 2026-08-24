/*
 * Item 4(a) - Arduino Uno, single-threaded busy loop.
 *
 * Same mechanism as esp32_a_busy_loop, ported to the Uno's ATmega328P:
 * every SAMPLE_PERIOD_MS, read 3 potentiometers and print the time elapsed
 * since the previous sample. Right after sampling, block the loop by
 * summing 1..N (N is swapped between runs to see its effect on the
 * achieved sampling period): the summation and the sampling share the
 * same single thread, so a large N delays the next sample directly.
 *
 * The Uno has no second core and no FreeRTOS, so there is no dual-core
 * (4b) variant for this board - only 4(a) and 4(c) apply, per the
 * assignment.
 *
 * Wiring: potentiometer wipers -> A0, A1, A2. Outer legs -> 5V and GND
 * (the Uno's ADC reference is 5V, unlike the ESP32's 3.3V).
 */

const int POT_PINS[3] = {A0, A1, A2};
const unsigned long SAMPLE_PERIOD_MS = 100;

// Swap this between runs: 1000000UL, 10000000UL, 100000000UL
const unsigned long SUM_LIMIT = 10000000UL;

unsigned long lastSampleMs = 0;

void setup() {
  Serial.begin(115200);
  lastSampleMs = millis();
}

void loop() {
  unsigned long now = millis();
  if (now - lastSampleMs >= SAMPLE_PERIOD_MS) {
    unsigned long dt = now - lastSampleMs;
    lastSampleMs = now;

    int a = analogRead(POT_PINS[0]); // 10-bit: 0-1023
    int b = analogRead(POT_PINS[1]);
    int c = analogRead(POT_PINS[2]);

    Serial.print(F("dt_ms="));
    Serial.print(dt);
    Serial.print(F(" pot1="));
    Serial.print(a);
    Serial.print(F(" pot2="));
    Serial.print(b);
    Serial.print(F(" pot3="));
    Serial.println(c);
  }

  // Blocking workload: on the Uno's 8-bit, 16 MHz ATmega328P this is far
  // slower per addition than on the ESP32's 32-bit Xtensa core, so the
  // same N produces a much larger delay here - see firmware/README.md.
  volatile unsigned long long sum = 0;
  for (unsigned long i = 0; i < SUM_LIMIT; i++) {
    sum += i;
  }
}
