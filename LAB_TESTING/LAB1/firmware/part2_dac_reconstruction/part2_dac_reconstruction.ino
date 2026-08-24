/*
 * LAB1, Part 2 - Signal reconstruction via the onboard DAC (ESP32).
 *
 * IMPORTANT DIFFERENCE FROM STM32: the ESP32's built-in DAC (GPIO25/26)
 * is only 8-bit (0-255), not 12-bit like the STM32's. The ADC still
 * captures at 12-bit resolution (0-4095) as required, but the
 * reconstructed DAC output necessarily has coarser amplitude resolution
 * than the capture - the 12-bit code is scaled down to 8 bits
 * (code >> 4) before being written out. This is a genuine hardware
 * limitation of the ESP32 vs. the STM32 the guide names, not a firmware
 * choice, and should be noted when comparing the reconstructed waveform's
 * fine detail against the DAC-reconstruction theory in
 * report/secciones/fundamento.tex.
 *
 * Same safe ISR pattern as part1_digitization.ino: the timer ISR only
 * captures + writes the DAC (both are quick register operations); Serial
 * transmission of the raw code happens in loop().
 *
 * Wiring:
 *   - ADC_PIN (GPIO34)  -> wave generator output (the signal to digitize).
 *   - DAC_PIN (GPIO25, one of the ESP32's two true DAC pins)
 *     -> oscilloscope channel 2, to compare against the generator's
 *        signal on channel 1.
 *   - DEBUG_PIN (GPIO5) -> oscilloscope channel 3 (optional), same 2 ms
 *     timing-verification edge as part 1.
 */

const int DEBUG_PIN = 5;
const int ADC_PIN = 34;
const int DAC_PIN = 25;
const uint32_t SAMPLE_PERIOD_US = 2000; // 2 ms -> 500 Hz
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

  uint16_t code = analogRead(ADC_PIN);   // 12-bit capture, 0-4095
  dacWrite(DAC_PIN, code >> 4);          // reconstruct at the DAC's native 8 bits, same ISR

  latestCode = code; // full 12-bit code still sent to the PC, for a fair comparison
  sampleReady = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}

void setup() {
  pinMode(DEBUG_PIN, OUTPUT);
  analogReadResolution(ADC_BITS);
  Serial.begin(115200);

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
