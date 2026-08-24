/*
 * LAB1, Part 1 - Periodic analog signal digitization.
 *
 * Target: ESP32-WROOM (32-bit Xtensa, dual core), via the Arduino core
 * for ESP32. The lab guide names an STM32 board for the PWM
 * reconstruction stage specifically (see part2_pwm_reconstruction.ino);
 * this port targets ESP32 hardware throughout instead, per the actual
 * board available for this project.
 *
 * - Hardware timer interrupt every 2 ms (500 samples/s), <=5% jitter budget.
 * - The ISR only toggles DEBUG_PIN (scope-verifiable edge-to-edge timing),
 *   reads the 12-bit ADC, and stores the code + a ready flag. Serial I/O
 *   is NOT done from the ISR itself (Serial.write is not guaranteed
 *   interrupt-safe on ESP32); loop() checks the flag and sends the frame,
 *   the same safe pattern used by esp32_c_interrupt.ino in
 *   THEORY/FIRST_ROUND/TEST/firmware.
 * - Unit conversion (code -> volts) is done PC-side by
 *   pc_logger/serial_logger.py.
 *
 * Wiring:
 *   - DEBUG_PIN (GPIO5) -> oscilloscope channel 1, to verify the 2 ms
 *     interrupt period.
 *   - ADC_PIN (GPIO34, ADC1-only, usable even with WiFi active unlike
 *     ADC2) -> wave generator output (sinusoid, 30-125 Hz for the main
 *     experiment; see report/secciones/resultados.tex) or a
 *     potentiometer wiper for preliminary testing.
 *   - ADC reference: ~3.3 V (the ESP32 ADC has known non-linearity vs.
 *     an ideal 12-bit converter, worth noting when comparing captured
 *     voltages against the generator's configured amplitude).
 *
 * Frame format (3 bytes, little-endian) - unchanged from the STM32
 * version, so pc_logger/serial_logger.py needs no changes:
 *   [0]      0xA5                     sync byte
 *   [1..2]   uint16_t raw_adc_code    0-4095 (12-bit)
 */

const int DEBUG_PIN = 5;
const int ADC_PIN = 34;
const uint32_t SAMPLE_PERIOD_US = 2000; // 2 ms -> 500 Hz
const float ADC_REF_VOLTS = 3.3f;
const int ADC_BITS = 12;

hw_timer_t *sampleTimer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;

volatile bool debugState = false;
volatile bool sampleReady = false;
volatile uint16_t latestCode = 0;

void IRAM_ATTR onSampleTick() {
  portENTER_CRITICAL_ISR(&timerMux);
  debugState = !debugState;
  digitalWrite(DEBUG_PIN, debugState ? HIGH : LOW);
  latestCode = analogRead(ADC_PIN); // 0-4095 with analogReadResolution(12)
  sampleReady = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}

void setup() {
  pinMode(DEBUG_PIN, OUTPUT);
  analogReadResolution(ADC_BITS);
  Serial.begin(115200); // see firmware/README.md for the byte-budget justification

  sampleTimer = timerBegin(1000000);              // 1 MHz -> 1 tick = 1 us (Arduino-ESP32 core 3.x timer API)
  timerAttachInterrupt(sampleTimer, &onSampleTick);
  timerAlarm(sampleTimer, SAMPLE_PERIOD_US, true, 0); // period in us, auto-reload, infinite reloads
}

void loop() {
  if (sampleReady) {
    portENTER_CRITICAL(&timerMux);
    uint16_t code = latestCode;
    sampleReady = false;
    portEXIT_CRITICAL(&timerMux);

    uint8_t frame[3] = {0xA5, (uint8_t)(code & 0xFF), (uint8_t)(code >> 8)};
    Serial.write(frame, sizeof(frame));
  }
}
