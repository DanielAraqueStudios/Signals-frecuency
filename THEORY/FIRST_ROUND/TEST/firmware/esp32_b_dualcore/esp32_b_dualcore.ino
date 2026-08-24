/*
 * Item 4(b) - ESP32-WROOM, dual-core FreeRTOS task split.
 *
 * Core 0 runs a dedicated task that samples the 3 potentiometers every
 * SAMPLE_PERIOD_MS and prints them; core 1 runs the default Arduino loop()
 * doing the same summation workload as 4(a)/4(c). Because sampling and the
 * summation run on separate cores, the summation should no longer block the
 * sampling task's timing the way it did in the single-threaded version.
 *
 * Wiring: same as 4(a) - GPIO34, GPIO35, GPIO32 -> potentiometer wipers.
 */

const int POT_PINS[3] = {34, 35, 32};
const unsigned long SAMPLE_PERIOD_MS = 100;

// Swap this between runs: 10000000UL, 1000000UL, 100000000UL
volatile unsigned long SUM_LIMIT = 10000000UL;

void samplingTask(void *parameter) {
  unsigned long lastSampleMs = millis();
  for (;;) {
    unsigned long now = millis();
    unsigned long dt = now - lastSampleMs;
    lastSampleMs = now;

    int a = analogRead(POT_PINS[0]);
    int b = analogRead(POT_PINS[1]);
    int c = analogRead(POT_PINS[2]);

    Serial.printf("[core0] dt_ms=%lu pot1=%d pot2=%d pot3=%d\n", dt, a, b, c);

    vTaskDelay(SAMPLE_PERIOD_MS / portTICK_PERIOD_MS);
  }
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);

  xTaskCreatePinnedToCore(
      samplingTask,
      "samplingTask",
      4096,
      NULL,
      1,
      NULL,
      0 /* pin to core 0 */
  );
}

void loop() {
  // Runs on core 1: the same blocking summation workload as 4(a)/4(c),
  // now isolated from the sampling task on core 0.
  volatile unsigned long long sum = 0;
  for (unsigned long i = 0; i < SUM_LIMIT; i++) {
    sum += i;
  }
}
