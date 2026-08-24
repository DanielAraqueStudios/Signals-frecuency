/*
 * LAB1, Part 1 - Periodic analog signal digitization.
 *
 * Target: a 32-bit microcontroller board (written for STM32 Nucleo-64,
 * e.g. F401RE/F411RE, via the STM32duino "Arduino_Core_STM32" core; the
 * pin names below use Arduino-style Nucleo aliases and should be adjusted
 * if a different STM32 board is used).
 *
 * - HardwareTimer interrupt every 2 ms (500 samples/s), <=5% jitter budget.
 * - Each interrupt: toggle DEBUG_PIN (scope-verifiable edge-to-edge timing)
 *   and read the ADC on ADC_PIN at 12-bit resolution.
 * - The raw 12-bit code is sent to the PC over Serial in a small binary
 *   frame; unit conversion (code -> volts) is done PC-side by
 *   pc_logger/serial_logger.py, using the documented ADC reference below.
 *
 * Wiring:
 *   - DEBUG_PIN (D5 / PA5, Nucleo user LED pin) -> oscilloscope channel 1,
 *     to verify the 2 ms interrupt period.
 *   - ADC_PIN (A0 / PA0) -> wave generator output (sinusoid, 30-125 Hz for
 *     the main experiment; see part 1 of the report for the full
 *     frequency table) or a potentiometer wiper for preliminary testing.
 *   - ADC reference: board Vref+ (typically 3.3 V) -> ADC_REF_VOLTS below.
 *
 * Frame format (3 bytes, little-endian):
 *   [0]      0xA5                     sync byte
 *   [1..2]   uint16_t raw_adc_code    0-4095 (12-bit)
 */

#include <HardwareTimer.h>

const int DEBUG_PIN = PA5;
const int ADC_PIN = PA0;
const uint32_t SAMPLE_PERIOD_US = 2000; // 2 ms -> 500 Hz
const float ADC_REF_VOLTS = 3.3f;       // must match the board's actual Vref+
const int ADC_BITS = 12;

HardwareTimer sampleTimer(TIM2);

volatile bool debugState = false;

void onSampleTick() {
  debugState = !debugState;
  digitalWrite(DEBUG_PIN, debugState ? HIGH : LOW);

  uint16_t code = analogRead(ADC_PIN); // 0-4095 with analogReadResolution(12)

  uint8_t frame[3] = {0xA5, (uint8_t)(code & 0xFF), (uint8_t)(code >> 8)};
  Serial.write(frame, sizeof(frame));
}

void setup() {
  pinMode(DEBUG_PIN, OUTPUT);
  analogReadResolution(ADC_BITS);
  Serial.begin(115200); // see report/secciones/metodologia.tex for the byte-budget justification

  sampleTimer.setOverflow(SAMPLE_PERIOD_US, MICROSEC_FORMAT);
  sampleTimer.attachInterrupt(onSampleTick);
  sampleTimer.resume();
}

void loop() {
  // All work happens in onSampleTick(); loop() is intentionally empty so
  // nothing here can compete with the timer interrupt for the sampling
  // period, unlike the busy-loop mechanism studied in THEORY/FIRST_ROUND/TEST.
}
