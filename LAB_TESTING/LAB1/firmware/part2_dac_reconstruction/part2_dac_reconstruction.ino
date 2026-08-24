/*
 * LAB1, Part 2 - Signal reconstruction via the onboard DAC.
 *
 * Same 2 ms timer interrupt and ADC capture as part1_digitization, but the
 * captured 12-bit code is also immediately written back out through the
 * board's DAC, concurrently with the interrupt (both happen inside the
 * same ISR, so there is no extra latency between capture and
 * reconstruction beyond the DAC's own settling time).
 *
 * Wiring:
 *   - ADC_PIN (A0 / PA0)  -> wave generator output (the signal to digitize).
 *   - DAC_PIN (A2 / PA4, the STM32's true DAC-capable pin on most Nucleo-64
 *     boards) -> oscilloscope channel 2, to compare against the generator's
 *     signal on channel 1.
 *   - DEBUG_PIN (D5 / PA5) -> oscilloscope channel 3 (optional), same
 *     2 ms timing-verification edge as part 1.
 *
 * The DAC on STM32 is typically 12-bit as well, so the ADC code can be
 * written back with no rescaling (DAC_PIN expects 0-4095 when
 * analogWriteResolution(12) is set).
 */

#include <HardwareTimer.h>

const int DEBUG_PIN = PA5;
const int ADC_PIN = PA0;
const int DAC_PIN = PA4;
const uint32_t SAMPLE_PERIOD_US = 2000; // 2 ms -> 500 Hz
const int RESOLUTION_BITS = 12;

HardwareTimer sampleTimer(TIM2);
volatile bool debugState = false;

void onSampleTick() {
  debugState = !debugState;
  digitalWrite(DEBUG_PIN, debugState ? HIGH : LOW);

  uint16_t code = analogRead(ADC_PIN);   // capture
  analogWrite(DAC_PIN, code);            // reconstruct, same ISR

  uint8_t frame[3] = {0xA5, (uint8_t)(code & 0xFF), (uint8_t)(code >> 8)};
  Serial.write(frame, sizeof(frame));
}

void setup() {
  pinMode(DEBUG_PIN, OUTPUT);
  analogReadResolution(RESOLUTION_BITS);
  analogWriteResolution(RESOLUTION_BITS);
  Serial.begin(115200);

  sampleTimer.setOverflow(SAMPLE_PERIOD_US, MICROSEC_FORMAT);
  sampleTimer.attachInterrupt(onSampleTick);
  sampleTimer.resume();
}

void loop() {}
