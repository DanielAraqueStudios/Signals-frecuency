/*
 * Item 4(c) - ESP32-WROOM, hardware-timer interrupt sampling.
 *
 * A hardware timer interrupt fires every SAMPLE_PERIOD_MS and only sets a
 * flag (ISRs must stay short: no Serial/analogRead inside the ISR itself).
 * loop() checks the flag, performs the actual potentiometer reads and the
 * Serial print, then goes back to the same blocking summation workload as
 * 4(a)/4(b). Since the timer is a hardware peripheral independent of the
 * main code path, the *timestamp* of each sample request stays accurate
 * even while loop() is busy summing; only the *processing* of that request
 * (the analogRead + print) is delayed until loop() next checks the flag.
 *
 * Wiring: same as 4(a) - GPIO34, GPIO35, GPIO32 -> potentiometer wipers.
 */

const int POT_PINS[3] = {34, 35, 32};
const unsigned long SAMPLE_PERIOD_MS = 100;

// Swap this between runs: 10000000UL, 1000000UL, 100000000UL
const unsigned long SUM_LIMIT = 10000000UL;

hw_timer_t *timer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;

volatile bool sampleReady = false;
volatile unsigned long lastIsrMs = 0;
volatile unsigned long isrDeltaMs = 0;

void IRAM_ATTR onTimer() {
  portENTER_CRITICAL_ISR(&timerMux);
  unsigned long now = millis();
  isrDeltaMs = now - lastIsrMs;
  lastIsrMs = now;
  sampleReady = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  lastIsrMs = millis();

  // 1 MHz timer clock -> 1 tick = 1 us (Arduino-ESP32 core 3.x timer API).
  timer = timerBegin(1000000);
  timerAttachInterrupt(timer, &onTimer);
  timerAlarm(timer, SAMPLE_PERIOD_MS * 1000, true, 0); // period in us, auto-reload, infinite reloads
}

void loop() {
  if (sampleReady) {
    portENTER_CRITICAL(&timerMux);
    unsigned long dt = isrDeltaMs;
    sampleReady = false;
    portEXIT_CRITICAL(&timerMux);

    int a = analogRead(POT_PINS[0]);
    int b = analogRead(POT_PINS[1]);
    int c = analogRead(POT_PINS[2]);

    Serial.printf("[isr] dt_ms=%lu pot1=%d pot2=%d pot3=%d\n", dt, a, b, c);
  }

  // Same blocking summation workload as 4(a)/4(b), left in loop() on
  // purpose: the interrupt still fires on time underneath it.
  volatile unsigned long long sum = 0;
  for (unsigned long i = 0; i < SUM_LIMIT; i++) {
    sum += i;
  }
}
