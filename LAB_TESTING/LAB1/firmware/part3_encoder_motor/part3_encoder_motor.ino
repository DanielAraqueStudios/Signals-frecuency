/*
 * LAB1, Part 3 - Encoder + DC gear-motor angular position/velocity (ESP32).
 *
 * Strategy: pulse counting within a fixed 5 ms window (200 samples/s),
 * using a pin-change interrupt on the encoder's A channel to increment a
 * counter, and the 5 ms timer interrupt to snapshot+reset that counter.
 * This "count pulses per interval" strategy (assignment's option 1) suits
 * a gear-motor's typical speed range better than "measure time between
 * pulses" (option 2), which is more accurate at very low speeds but noisy
 * at the higher, more constant speeds a loaded gear-motor typically runs
 * at; swap strategies in countEncoderPulse()/onSampleTick() if the actual
 * motor's speed range calls for it (see report/secciones/metodologia.tex).
 *
 * PULSES_PER_REV must be set from the encoder's actual datasheet/count
 * (verify with a tachometer per the assignment) before angle/velocity
 * values are meaningful; it is left as a placeholder below.
 *
 * Wiring: encoder channel A -> ENCODER_A_PIN (any GPIO usable with
 * attachInterrupt), channel B -> ENCODER_B_PIN (used only for direction
 * sign, not counted here), motor driver PWM/direction pins -> per the
 * driver module's own datasheet.
 *
 * Frame format (5 bytes, little-endian) - unchanged from the STM32
 * version:
 *   [0]     0xC5                sync byte
 *   [1..2]  int16_t pulse_count  signed pulses counted in the last 5 ms
 *   [3..4]  uint16_t reserved    0x0000
 */

const int ENCODER_A_PIN = 4;
const int ENCODER_B_PIN = 16;
const uint32_t SAMPLE_PERIOD_US = 5000; // 5 ms -> 200 Hz

// TODO: set from the actual encoder's datasheet / tachometer-verified count.
const int PULSES_PER_REV = 0;

hw_timer_t *sampleTimer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;
volatile int32_t pulseCount = 0;

volatile bool sampleReady = false;
volatile int16_t latestSignedCount = 0;

void IRAM_ATTR countEncoderPulse() {
  bool forward = digitalRead(ENCODER_B_PIN) == HIGH;
  portENTER_CRITICAL_ISR(&timerMux);
  pulseCount += forward ? 1 : -1;
  portEXIT_CRITICAL_ISR(&timerMux);
}

void IRAM_ATTR onSampleTick() {
  portENTER_CRITICAL_ISR(&timerMux);
  int32_t count = pulseCount;
  pulseCount = 0;
  latestSignedCount = (int16_t)count; // pulses in the last 5 ms window
  sampleReady = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}

void setup() {
  pinMode(ENCODER_A_PIN, INPUT_PULLUP);
  pinMode(ENCODER_B_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A_PIN), countEncoderPulse, RISING);

  Serial.begin(115200);

  sampleTimer = timerBegin(1000000);              // 1 MHz -> 1 tick = 1 us (Arduino-ESP32 core 3.x timer API)
  timerAttachInterrupt(sampleTimer, &onSampleTick);
  timerAlarm(sampleTimer, SAMPLE_PERIOD_US, true, 0); // period in us, auto-reload, infinite reloads
}

void loop() {
  if (sampleReady) {
    portENTER_CRITICAL(&timerMux);
    int16_t signedCount = latestSignedCount;
    sampleReady = false;
    portEXIT_CRITICAL(&timerMux);

    uint8_t frame[5] = {
        0xC5,
        (uint8_t)(signedCount & 0xFF), (uint8_t)(signedCount >> 8),
        0x00, 0x00};
    Serial.write(frame, sizeof(frame));
  }
}
